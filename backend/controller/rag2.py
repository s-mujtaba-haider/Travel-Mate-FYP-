import os
import json
import pandas as pd
import hashlib
from uuid import UUID
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Tuple
from controller import PlacesRAGDatabase

class Place(BaseModel):
    """Pydantic model for a single place"""
    id: str
    display_name: str
    formatted_address: str
    lat: float
    lng: float
    types: Optional[str] = None  # Changed to Optional[str]
    rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    city: str
    main_category: str

class PlaceResponse(BaseModel):
    """Pydantic model for a place response"""
    place_id: str = Field(..., description="Unique identifier of the place")
    name: str = Field(..., description="Name of the place")
    address: str = Field(..., description="Full address")
    location: Dict[str, Union[str, float]] = Field(..., description="Location details")
    category: str = Field(..., description="Main category of the place")
    types: Optional[str] = Field(None, description="Types/tags for the place")  # Changed to Optional[str]
    rating_info: Dict[str, Optional[Union[float, int, str]]] = Field(
        default_factory=lambda: {
            "rating": None,
            "review_count": None,
            "rating_text": "No rating available"
        },
        description="Rating information"
    )

class QueryResponse(BaseModel):
    """Pydantic model for the complete query response"""
    message: str = Field(..., description="A natural language summary of the results")
    places: List[PlaceResponse] = Field(default_factory=list, description="List of matching places")
    context: Optional[str] = Field(None, description="Context from previous conversation if relevant")
    applied_filters: Optional[Dict] = Field(
        default_factory=dict,
        description="Filters applied to the query"
    )
    filter_action: Optional[str] = Field(
        default="keep",
        description="Filter action: update/clear/keep"
    )
    # error_context: Optional[Dict] = Field(
    #     default_factory=lambda: {
    #         "has_error": False,
    #         "invalid_filters": [],
    #         "suggestions": []
    #     },
    #     description="Error context for invalid filters"
    # )


class DatabaseIntegratedRAG:
    def __init__(self, 
                 csv_path: str, 
                 openai_api_key: str, 
                 db: PlacesRAGDatabase,
                 embeddings_dir: str = "embeddings"):
        """Initialize RAG system with database integration"""
        self.csv_path = csv_path
        self.embeddings_dir = embeddings_dir
        self.db = db
        os.environ['OPENAI_API_KEY'] = openai_api_key
        
        # Initialize LLM components
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
        self.output_parser = PydanticOutputParser(pydantic_object=QueryResponse)
        
        # Load and process data
        self.df = pd.read_csv(csv_path)
        self.valid_cities = set(self.df['city'].unique())
        self.valid_categories = set(self.df['main_category'].unique())
        self.valid_types = set(self.df['types'].dropna().unique())
        
        # Setup core components
        self.setup_vectorstore()
        self.setup_prompt_templates()

    def setup_vectorstore(self):
        """Setup vector store with same logic as before"""
        embeddings_path = self._get_embeddings_path()
        try:
            self.vectorstore = FAISS.load_local(embeddings_path, self.embeddings)
        except Exception as e:
            documents = self._create_documents()
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            self.vectorstore.save_local(embeddings_path)

    def _get_embeddings_path(self) -> str:
        """Calculate embeddings path (unchanged)"""
        with open(self.csv_path, 'rb') as f:
            csv_hash = hashlib.md5(f.read()).hexdigest()
        return os.path.join(self.embeddings_dir, f"places_embeddings_{csv_hash}")

    def _create_documents(self) -> List[Document]:
        """Create documents (unchanged)"""
        documents = []
        for _, row in self.df.iterrows():
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
            Category: {place.main_category}
            Type: {place.types if place.types else 'Not specified'}
            Rating: {place.rating if place.rating else 'No rating'} ({place.user_rating_count if place.user_rating_count else 0} reviews)
            """
            
            metadata = place.model_dump()
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents

    def setup_prompt_templates(self):
        """Setup prompt templates (unchanged)"""
        self.response_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant that provides information about places and locations.
            Use the chat history to understand context and previous questions.
            
            Current filters in use:
            {current_filters}
            
            Analyze the context, chat history, and user query, then provide a response in the following JSON format:
            
            {format_instructions}
            
            Chat History:
            {chat_history}
            
            Context about places:
            {context}
            
            User Query: {query}
            
            Instructions:
            1. Use chat history to maintain context
            2. Include only relevant places (max 5)
            3. If no matching places are found, return empty places list and appropriate message
            4. Keep any valid filters for future use
            5. Set filter_action appropriately
            6. Handle null values gracefully in all fields
            """)]
        )

    def _validate_and_extract_filters(self, query: str, current_filters: Dict) -> Tuple[Dict, Dict]:
        """Extract and validate filters (similar logic but consider current filters)"""
        query_lower = query.lower()
        valid_filters = current_filters.copy()  # Start with current filters
        # invalid_filters = {}
        
        # City validation
        detected_city = next((city for city in self.valid_cities 
                            if city.lower() in query_lower), None)
        
        valid_filters['city'] = detected_city if detected_city else None
        # else:
            # potential_city = next((word for word in query_lower.split() 
                                #  if word.istitle() and word not in self.valid_cities), None)
            # if potential_city:
                # invalid_filters['city'] = potential_city
        
        detected_category = next((category for category in self.valid_categories 
                                if category.lower() in query_lower), None)
        
        valid_filters['category'] = detected_category if detected_category else None
        # else:
        #     words = query_lower.split()
        #     for i in range(len(words)-1):
        #         potential_category = f"{words[i]} {words[i+1]}"
        #         if any(cat.lower().startswith(potential_category) for cat in self.valid_categories):
        #             invalid_filters['category'] = potential_category.title()
        
        # Types validation - handle as single string
        detected_type = next((type_ for type_ in self.valid_types 
                            if type_.lower() in query_lower), None)
        
        valid_filters['types'] = detected_type if detected_type else None
        # else:
        #     potential_type = next((word for word in query_lower.split() 
        #                          if any(t.lower().endswith(word) for t in self.valid_types)), None)
            # if potential_type:
            #     invalid_filters['types'] = None
        
        # Rating filter
        if any(word in query_lower for word in ['best', 'top', 'highest rated']):
            valid_filters['min_rating'] = 4.0
        
        return valid_filters
        
    async def answer_query(
        self,
        query: str,
        user_id: UUID,
        session_id: Optional[UUID] = None
    ) -> Tuple[QueryResponse, UUID]:
        """Process query with database integration"""
        # Get or create session
        session = await self.db.get_or_create_session(user_id)
        session_id = session.session_id

        # Get chat history from database
        chat_history = await self.db.get_chat_history(session_id)

        # Get current filters from last assistant message
        current_filters = {}
        if chat_history:
            for msg in reversed(chat_history):
                if isinstance(msg, AIMessage):
                    try:
                        content = json.loads(msg.content)
                        current_filters = content.get('applied_filters', {})
                        break
                    except:
                        continue

        # Process filters
        if self._should_clear_filters(query):
            current_filters = {}
            filter_action = "clear"
        else:
            valid_filters = self._validate_and_extract_filters(query, current_filters)
            # suggestions = self._get_similar_suggestions(invalid_filters)
            
            if valid_filters != current_filters:
                filter_action = "update"
                current_filters = valid_filters
            else:
                filter_action = "keep"

        # Search places
        relevant_docs = self.search_places(query, chat_history, current_filters)
        
        # Prepare context for LLM
        # context = "\n\n".join(doc.page_content for doc in relevant_docs) if relevant_docs else ""
        context = "\n\n".join(doc.metadata for doc in relevant_docs) if relevant_docs else ""
        # invalid_filter_context = {
        #     "has_error": bool(invalid_filters) if 'invalid_filters' in locals() else False,
        #     "invalid_filters": list(invalid_filters.keys()) if 'invalid_filters' in locals() else [],
        #     "suggestions": suggestions if 'suggestions' in locals() else {}
        # }

        # Generate response
        chain = self.response_template | self.llm | self.output_parser
        response = await chain.ainvoke({
            "context": context,
            "query": query,
            "chat_history": chat_history,
            "current_filters": json.dumps(current_filters, indent=2),
            # "invalid_filters": json.dumps(invalid_filter_context, indent=2),
            "format_instructions": self.output_parser.get_format_instructions()
        })
        # response = await self.response_template.ainvoke({
        #     "context": context,
        #     "query": query,
        #     "chat_history": chat_history,
        #     "current_filters": json.dumps(current_filters, indent=2),
        #     "invalid_filters": json.dumps(invalid_filter_context, indent=2),
        #     "format_instructions": self.output_parser.get_format_instructions()
        # })
        parsed_response = self.output_parser.parse(response)

        # Save assistant message
        # await self.db.add_message(
        #     session_id=session_id,
        #     role="assistant",
        #     content={
        #         "message": parsed_response.message,
        #         "places": [place.model_dump() for place in parsed_response.places],
        #         "applied_filters": current_filters,
        #         "filter_action": filter_action,
        #         "error_context": invalid_filter_context
        #     }
        # )

        return parsed_response, session_id

    # Helper methods remain largely unchanged
    def _should_clear_filters(self, query: str) -> bool:
        reset_phrases = {'show everything', 'any place', 'all places', 'reset', 'start over', 'clear filters'}
        return any(phrase in query.lower() for phrase in reset_phrases)

    # def _get_similar_suggestions(self, invalid_filters: Dict) -> Dict[str, List[str]]:
    #     """Get similar valid suggestions for invalid filters"""
    #     suggestions = {}
        
    #     for filter_type, invalid_value in invalid_filters.items():
    #         if filter_type == 'city':
    #             similar_cities = [
    #                 city for city in self.valid_cities
    #                 if any(word in city.lower() for word in invalid_value.lower().split())
    #             ][:3]
    #             if similar_cities:
    #                 suggestions['city'] = similar_cities
            
    #         elif filter_type == 'category':
    #             similar_categories = [
    #                 category for category in self.valid_categories
    #                 if any(word in category.lower() for word in invalid_value.lower().split())
    #             ][:3]
    #             if similar_categories:
    #                 suggestions['category'] = similar_categories
            
    #         elif filter_type == 'types':
    #             similar_types = [
    #                 type_ for type_ in self.valid_types
    #                 if invalid_value.lower() in type_.lower()
    #             ][:3]
    #             if similar_types:
    #                 suggestions['types'] = similar_types
        
    #     return suggestions

    def search_places(self, query: str, chat_history: List = None, filters: Dict = None, k: int = 5) -> List[Document]:
        """Search for relevant places with filters and chat context"""
        if chat_history:
            recent_context = " ".join([msg.content for msg in chat_history[-4:]])
            enhanced_query = f"{recent_context} {query}"
        else:
            enhanced_query = query

        # Initial search
        docs = self.vectorstore.similarity_search(enhanced_query, k=k*2)
        
        if not filters:
            return docs[:k]
        
        # Apply filters
        filtered_docs = []
        for doc in docs:
            matches = True
            for key, value in filters.items():
                if key == 'min_rating':
                    if not doc.metadata.get('rating') or doc.metadata['rating'] < value:
                        matches = False
                        break
                elif doc.metadata.get(key) != value:
                    matches = False
                    break
            if matches:
                filtered_docs.append(doc)
        
        return filtered_docs[:k]