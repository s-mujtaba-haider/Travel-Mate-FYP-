import os
import json
import pandas as pd
import hashlib
import traceback
from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from controller import EmbeddingsError, DataLoadError, APIKeyError, RAGError, SearchError, ResponseGenerationError, DatabaseError
from controller.database import Session as db_session
from models.chat import Message


class Place(BaseModel):
    """Pydantic model for a single place"""
    id: str
    display_name: str
    formatted_address: str
    lat: float
    lng: float
    types: Optional[str] = None
    rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    city: str
    main_category: str

class PlaceResponse(BaseModel):
    """Pydantic model for a place response"""
    place_id: str = Field(..., description="identifier of the place")
    name: str = Field(..., description="Name of the place")
    address: str = Field(..., description="Full address")
    lat: Optional[float] = Field(None, description="Location lattitide details")
    lng: Optional[float] = Field(None, description="Location longitude details")
    city: str = Field(..., description="City where the place is located")
    main_category: str = Field(..., description="Main category of the place")
    types: Optional[str] = Field(None, description="Types/tags for the place")
    rating: Optional[float] = Field(None, description="Rating of the place")
    review_count: Optional[int] = Field(None, description="Number of reviews for the place")

class QueryResponse(BaseModel):
    """Pydantic model for the complete query response"""
    message: str = Field(..., description="A natural language summary of the results")
    places: List[PlaceResponse] = Field(default_factory=list, description="List of matching places")
    context: Optional[str] = Field(None, description="Context from previous conversation if relevant")
    applied_filters: Optional[Dict] = Field(default_factory=dict, description="Filters applied to the query")
    filter_action: Optional[str] = Field(default="keep", description="Filter action: update/clear/keep")

class PlacesEmbeddingsGenerator:
    """Handles creation and management of embeddings for places data"""
    def __init__(self, embeddings_dir: str = "controller/embeddings"):
        try:
            self.embeddings_dir = embeddings_dir
            self.embeddings = OpenAIEmbeddings()
            os.makedirs(embeddings_dir, exist_ok=True)
        except Exception as e:
            print(traceback.format_exc(1))
            raise EmbeddingsError(f"Failed to initialize embeddings generator: {str(e)}")
    
    def _get_embeddings_path(self, csv_path: str) -> str:
        """Generate a unique path for embeddings based on CSV content hash"""
        with open(csv_path, 'rb') as f:
            csv_hash = hashlib.md5(f.read()).hexdigest()
        return os.path.join(self.embeddings_dir, f"places_embeddings_{csv_hash}")
    
    def _create_documents(self, df: pd.DataFrame) -> List[Document]:
        """Create document objects from DataFrame rows"""
        documents = []
        for _, row in df.iterrows():
            place = Place(
                id=str(row['id']),
                display_name=row['displayName'],
                formatted_address=row['formattedAddress'],
                lat=float(row['lat']),
                lng=float(row['lng']),
                types=row['types'] if pd.notnull(row['types']) else None,
                rating=row['rating'] if pd.notnull(row['rating']) else None,
                user_rating_count=int(row['userRatingCount']) if pd.notnull(row['userRatingCount']) else None,
                city=row['city'],
                main_category=row['main_category']
            )
            
            content = f"""
            Name: {place.display_name}
            Address: {place.formatted_address}
            City: {place.city}
            main_category: {place.main_category}
            Type: {place.types if place.types else 'Not specified'}
            Rating: {place.rating if place.rating else 'No rating'} ({place.user_rating_count if place.user_rating_count else 0} reviews)
            """
            
            metadata = place.model_dump()
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents

    def generate_or_load_vectorstore(self, csv_path: str) -> FAISS:
        """Create or load vector store from places data"""
        try:
            embeddings_path = self._get_embeddings_path(csv_path)
            
            try:
                print(f"Loading embeddings from {embeddings_path}")
                vectorstore = FAISS.load_local(embeddings_path, self.embeddings, allow_dangerous_deserialization=True)
                print("Successfully loaded existing embeddings")
                return vectorstore
            except Exception as load_error:
                print(f"Creating new embeddings (reason: {str(load_error)})")
                df = pd.read_csv(csv_path)
                documents = self._create_documents(df)
                print(f"Generated {len(documents)} documents")
                vectorstore = FAISS.from_documents(documents, self.embeddings)
                print("Successfully created new embeddings")
                os.makedirs(embeddings_path, exist_ok=True)
                vectorstore.save_local(embeddings_path)
                print(f"Saved new embeddings to {embeddings_path}")
                return vectorstore
                
        except pd.errors.EmptyDataError:
            print(traceback.format_exc(1))
            raise DataLoadError("CSV file is empty")
        except pd.errors.ParserError:
            print(traceback.format_exc(1))
            raise DataLoadError("Invalid CSV format")
        except Exception as e:
            print(traceback.format_exc(1))
            raise EmbeddingsError(f"Failed to generate or load vectorstore: {str(e)}")

class RAGPipeline:
    """Main RAG system integrated with database"""
    def __init__(self, csv_path: str, openai_api_key: str, embeddings_dir: str = "controller/embeddings"):
        try:
            if not openai_api_key:
                print(traceback.format_exc(1))
                raise APIKeyError("OpenAI API key is required")
            
            self.csv_path = csv_path
            os.environ['OPENAI_API_KEY'] = openai_api_key
            
            # Initialize components
            self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.1)
            self.output_parser = PydanticOutputParser(pydantic_object=QueryResponse)
            
            # Load and process data
            try:
                self.df = pd.read_csv(csv_path)
                if self.df.empty:
                    print(traceback.format_exc(1))
                    raise DataLoadError("CSV file is empty")
                
                self.valid_cities = set(self.df['city'].unique())
                self.valid_categories = set(self.df['main_category'].unique())
                self.valid_types = set(self.df['types'].dropna().unique())
                
            except FileNotFoundError:
                print(traceback.format_exc(1))
                raise DataLoadError(f"CSV file not found: {csv_path}")
            except pd.errors.EmptyDataError:
                print(traceback.format_exc(1))
                raise DataLoadError("CSV file is empty")
            except pd.errors.ParserError:
                print(traceback.format_exc(1))
                raise DataLoadError("Invalid CSV format")
            
            # Generate or load embeddings
            embeddings_generator = PlacesEmbeddingsGenerator(embeddings_dir)
            self.vectorstore = embeddings_generator.generate_or_load_vectorstore(csv_path)
            self.db_manager: Session = db_session()
            self.setup_prompt_templates()
            
        except RAGError:
            print(traceback.format_exc(1))
            raise
        except Exception as e:
            print(traceback.format_exc(1))
            raise RAGError(f"Failed to initialize RAG system: {str(e)}", "INITIALIZATION_ERROR")

    def setup_prompt_templates(self):
        """Setup prompt templates for query processing"""
        self.response_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful places recommender assistant for locations in Pakistan.  
            Only respond based on the provided relevent places and filters. **Do not invent places.**  

            ### **Response Rules**:
            1. **If places are available**, return up to {n_places}, prioritizing higher ratings and review counts.
            2. **If no places match**, return an empty `"places"` list with an appropriate `"message"`. **Do not generate fake places.**
            3. **Do not assume information**—base responses strictly on provided data.

            ### **Response Format**:
            ```json
                {{  
                "message": "Conversational response explaining results",  
                "places": [  
                    {{  
                        "place_id": "unique identifier",  
                        "name": "place name",  
                        "address": "full address",  
                        "lat": float | null,  
                        "lng": float | null,  
                        "city": "city name",  
                        "main_category": "public places | restaurants | hotels | mosques or masjid",  
                        "types": "comma-separated subcategories | null",  
                        "rating": float | null,  
                        "review_count": int | null  
                    }}  
                ],  
                "context": "Relevant prior conversation context",  
                "applied_filters": {{  
                    "city": "string | null",  
                    "main_category": "string | null",  
                    "types": "string | null",  
                    "min_rating": float | null  
                }},  
                "filter_action": "update | clear | keep"  
            }}    

            **Filter Actions:**  
            - **update** → User specifies new/modified filters.  
            - **clear** → User resets search.  
            - **keep** → User refines existing filters or follows up.  

            **Query Interpretation:**  
            - **Location-related** → Update `city`.  
            - **Category mention** → Update `main_category`.  
            - **Feature requests** → Update `types`.  
            - **Quality mentions** → Update `min_rating`.  
            - Maintain filters unless explicitly changed.  

            **Error Handling:**  
            - Out-of-Pakistan queries → Explain limitation.  
            - Ambiguous queries → Ask clarifying questions.  
            - No results → Suggest broader search criteria.  
            """),

                ("user", """
                User Query: {query}
                Relevent places: {context}  
                Current Filters: {current_filters}    
                Chat History: {chat_history}
            """)
            ])

        # self.response_template = ChatPromptTemplate.from_messages([
        #     ("system", """You are a helpful places recommender assistant that provides information about places and locations in Pakistan.
        #     You must:
        #     1. Respond in the following JSON format:

        #     {{
        #         "message": "A natural language summary of the results, including feedback about invalid query or out of scope if any",
        #         "places": [
        #             {{
        #                 "place_id": "unique identifier",
        #                 "name": "place name",
        #                 "address": "full address",
        #                 "lat": "float or null. place latitude",
        #                 "lng": "float or null place longitude",
        #                 "city": "city name",
        #                 "main_category": "main category",
        #                 "types": "type string or null. tags for the place",
        #                 "rating": "float or null. place rating",
        #                 "review_count": "int or null. number of reviews"
        #             }}
        #         ],
        #         "context": "Reference to previous conversation if relevant",
        #         "applied_filters": {{
        #             "city": string or null = identified city from query,
        #             "main_category": string or null = (selcted from: public places, restaurants, hotels, mosques or masjid),
        #             "types": string or null,
        #             "min_rating": float or null
        #         }},
        #         "filter_action": "update/clear/keep"
        #     }}
        #     2. Prioritize the most relevant and up-to-date data provided in the current query and context over chat history.
        #     3. if no context places provided, return an empty places list and an appropriate message.
        #     4. Use chat history only to maintain continuity if it aligns with the current query.
        #     5. Provide responses in the specified JSON format.
        #     6. Include only relevant places (max {n_places}), focusing on data directly related to the query and filters.
        #     7. If no matching places are found, return an empty places list and an appropriate message.
        #     8. Keep any valid filters for future use, and also update if some filter is missing.
        #     9. Set filter_action appropriately based on the user's query and current filters.
        #     10. Handle null values gracefully in all fields."""),
        #     ("user", """
        #         Chat History:
        #         {chat_history}

        #         Context about places:
        #         {context}

        #         Current filters in use:
        #         {current_filters}

        #         User Query: {query}
        #         """)
        #     ]
        # )

    async def get_chat_history(self, session_id: UUID, limit: int = 6) -> List[Dict]:
        """Get recent chat history for a session"""
        try:
            messages = self.db_manager.query(Message)\
                .filter(Message.session_id == session_id)\
                .order_by(Message.timestamp.desc())\
                .limit(limit)\
                .all()
            
            last_filter = self.db_manager.query(Message.applied_filters)\
                .filter(Message.session_id == session_id, Message.role == 'assistant')\
                .order_by(Message.timestamp.desc())\
                .first()
            
            history = []
            for msg in messages:
                if msg.role == "human":
                    history.append(HumanMessage(content=msg.content["message"]))
                else:
                    history.append(AIMessage(content=json.dumps(msg.content)))
            
            return list(reversed(history)), last_filter
            
        except Exception as e:
            print(traceback.format_exc(1))
            raise DatabaseError(f"Failed to fetch chat history: {str(e)}")

    def _should_clear_filters(self, query: str) -> bool:
        """Check if query indicates filter reset"""
        reset_phrases = {'show everything', 'any place', 'all places', 'reset', 'start over', 'clear filters'}
        return any(phrase in query.lower() for phrase in reset_phrases)
    

    def _validate_and_extract_filters(self, query: str, current_filters: Dict) -> Dict:
        """Extract and validate filters dynamically while retaining existing ones."""
        query_lower = query.lower()
        valid_filters = current_filters.copy()
        
        # Define category mappings with synonyms and subcategories
        category_mapping = {
            'public places': [
                'park', 'parks', 'garden', 'gardens', 'plaza', 'square', 'museum', 
                'gallery', 'beach', 'beaches', 'landmark', 'monuments', 'library',
                'public space', 'community center', 'playground'
            ],
            'restaurants': [
                'eatery', 'cafe', 'diner', 'dining', 'bistro', 'food', 'fast food',
                'pizzeria', 'steakhouse', 'bakery', 'coffee shop', 'bar', 'pub',
                'buffet', 'grill', 'bbq', 'seafood place'
            ],
            'hotels': [
                'motel', 'inn', 'resort', 'lodge', 'accommodation', 'stay', 'hostel',
                'guesthouse', 'bed and breakfast', 'b&b', 'airbnb', 'apartment',
                'lodging', 'place to stay'
            ],
            'mosques': [
                'masjid', 'mosque', 'islamic center', 'prayer hall', 'prayer room',
                'jummah', 'religious place', 'worship place'
            ]
        }
        
        # Define other filter mappings
        filter_mapping = {
            'city': self.valid_cities,
            'types': self.valid_types,
        }
        
        # Check for main_category using the expanded mapping
        for main_category, synonyms in category_mapping.items():
            # Check if the main category itself is in the query
            if main_category.lower() in query_lower:
                valid_filters['main_category'] = main_category
                break
                
            # Check if any synonym is in the query
            for synonym in synonyms:
                if synonym.lower() in query_lower:
                    valid_filters['main_category'] = main_category
                    break
            
            # If we found a match, no need to check other categories
            if valid_filters.get('main_category') == main_category:
                break
        
        # Process other filters normally
        for filter_key, valid_values in filter_mapping.items():
            detected_value = next(
                (value for value in valid_values if value.lower() in query_lower), 
                None
            )
            # Update only if a valid value is detected
            if detected_value:
                valid_filters[filter_key] = detected_value
        
        # Add additional custom rules
        custom_rules = [
            {
                'keywords': ['best', 'top', 'highest rated'],
                'filter_key': 'min_rating',
                'value': 4.0,
            },
            # Add more custom rules as needed
        ]
        
        for rule in custom_rules:
            if any(keyword in query_lower for keyword in rule['keywords']):
                valid_filters[rule['filter_key']] = rule['value']
        
        return valid_filters
    # def _validate_and_extract_filters(self, query: str, current_filters: Dict) -> Dict:
    #     """Extract and validate filters dynamically while retaining existing ones."""
    #     query_lower = query.lower()
    #     valid_filters = current_filters.copy()
        
    #     # Define filter mappings
    #     filter_mapping = {
    #         'city': self.valid_cities,
    #         'main_category': self.valid_categories,
    #         'types': self.valid_types,
    #     }
        
    #     # Dynamically check for filters
    #     for filter_key, valid_values in filter_mapping.items():
    #         detected_value = next(
    #             (value for value in valid_values if value.lower() in query_lower), 
    #             None
    #         )
    #         # Update only if a valid value is detected
    #         if detected_value:
    #             valid_filters[filter_key] = detected_value
        
    #     # Add additional custom rules
    #     custom_rules = [
    #         {
    #             'keywords': ['best', 'top', 'highest rated'],
    #             'filter_key': 'min_rating',
    #             'value': 4.0,
    #         },
    #         # Add more custom rules as needed
    #     ]
        
    #     for rule in custom_rules:
    #         if any(keyword in query_lower for keyword in rule['keywords']):
    #             valid_filters[rule['filter_key']] = rule['value']
        
    #     return valid_filters

    # def search_places(self, query: str, filters: Dict = None, k: int = 5) -> List[Document]:
    #     """Search for relevant places with filters"""
    #     try:
    #         # enhanced_query = f"{' '.join([msg.content for msg in chat_history[-4:]])} {query}" if chat_history else query
    #         docs = self.vectorstore.similarity_search(query, k=k*2)
    #         print(f"Found {len(docs)} similar places")
    #         print(f"docs: {docs}")
    #         if not filters:
    #             return docs[:k]

    #         filtered_docs = [
    #             doc for doc in docs
    #             if all(
    #                 (key != 'min_rating' and doc.metadata.get(key) == value) or
    #                 (key == 'min_rating' and doc.metadata.get('rating', 0) >= value)
    #                 for key, value in filters.items()
    #                 if value is not None
    #             )
    #         ]
            
    #         return filtered_docs[:k]
            
    #     except Exception as e:
    #         raise SearchError(f"Failed to search places: {str(e)}")

    def search_places(self, query: str, filters: Optional[Dict] = None, k: int = 5) -> List[Document]:
        """Search for relevant places with metadata filtering"""
        try:
            # Prepare metadata filter dict
            metadata_filter = {}
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        if key == 'min_rating':
                            # For min_rating, we'll still need post-processing as FAISS doesn't support range queries
                            continue
                        metadata_filter[key] = value
            # remove types key from metadata_filter
            if metadata_filter.get('types'):
                metadata_filter.pop('types')

            # Use FAISS's built-in metadata filtering
            docs = self.vectorstore.similarity_search(
                query,
                k=k*2,  # Get more results initially since we might need to filter by rating
                filter=metadata_filter if metadata_filter else None
            )
            # print(f"Found {docs} similar places")
            # Post-process only for min_rating if needed
            if filters and filters.get('min_rating'):
                docs = [
                    doc for doc in docs 
                    if doc.metadata.get('rating', 0) >= filters['min_rating']
                ]
            
            return docs[:k+2] if docs else []
        except Exception as e:
            print(traceback.format_exc(1))
            raise SearchError(f"Failed to search places: {str(e)}")
    
    async def answer_query(self, query: str,n_places: int = 5, session_id: Optional[UUID] = None) -> Tuple[QueryResponse, UUID]:
        """Process query and generate response"""
        try:
            if not query.strip():
                raise ValueError("Query cannot be empty")
            
            chat_history, last_filter = await self.get_chat_history(session_id)

            current_filters = {}
            
            # Get current filters from last assistant message
            if last_filter:
                current_filters = last_filter[0]
            else:
                current_filters = {}
            
            # Process filters
            filter_action = "clear" if self._should_clear_filters(query) else "update"
            current_filters = {} if filter_action == "clear" else self._validate_and_extract_filters(query, current_filters)
            
            # Search and generate response
            try:
                # print(f"Searching for places with query: {query}")
                # print(f"Current filters: {current_filters}")
                # print(f"Chat history: {chat_history}")
                relevant_docs = self.search_places(query=query,filters=current_filters, k=n_places)
                # print(f"Found {len(relevant_docs)} relevant places")
                # print(f"relevent docs: {relevant_docs}")
                # context = "\n\n".join(doc.page_content for doc in relevant_docs) if relevant_docs else ""
                
                context = "\n\n".join(json.dumps(doc.metadata) for doc in relevant_docs) if relevant_docs else "No places found"
                chain = self.response_template | self.llm | self.output_parser
                response = await chain.ainvoke({
                    "context": context,
                    "query": query,
                    "chat_history": chat_history,
                    "current_filters": json.dumps(current_filters, indent=2),
                    "n_places": n_places,
                    # "format_instructions": self.output_parser.get_format_instructions()
                })
                
                return response.model_dump()
                
            except Exception as search_error:
                print(traceback.format_exc(1))
                raise SearchError(f"Failed to search or generate response: {str(search_error)}")
            
        except RAGError:
            print(traceback.format_exc(1))
            raise RAGError("INVALID_INPUT")
        except ValueError as ve:
            print(traceback.format_exc(1))
            raise RAGError(str(ve), "INVALID_INPUT")
        except Exception as e:
            print(traceback.format_exc(1))
            raise ResponseGenerationError(f"Failed to process query: {str(e)}")