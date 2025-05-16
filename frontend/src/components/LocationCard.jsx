import React from 'react';
import { Navigation } from 'lucide-react';

const LocationCard = ({ place }) => {
  const handleOpenDirections = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        const { latitude, longitude } = position.coords;
        const url = `https://www.google.com/maps/dir/${latitude},${longitude}/${place.lat},${place.lng}`;
        window.open(url, '_blank');
      }, (error) => {
        const url = `https://www.google.com/maps/dir//${place.lat},${place.lng}`;
        window.open(url, '_blank');
      });
    } else {
      const url = `https://www.google.com/maps/dir//${place.lat},${place.lng}`;
      window.open(url, '_blank');
    }
  };

  return (
    <div className="p-4 bg-gray-800 rounded-lg shadow-lg mb-4">
      <div className="p-4">
        <h3 className="font-medium text-lg">
          {place.name} {place.rating && `(${place.rating} ⭐)`}
        </h3>
        <p className="text-gray-300 text-sm mt-1">{place.address}</p>
        <button
          onClick={handleOpenDirections}
          className="self-end mt-2 flex items-center gap-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-md text-sm transition-colors"
        >
          <Navigation className="w-3 h-3" />
          <span>Get Directions</span>
        </button>
      </div>
    </div>
  );
};

export default LocationCard;