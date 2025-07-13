import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [stations, setStations] = useState([]);
  const [currentStation, setCurrentStation] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [volume, setVolume] = useState(0.7);
  const [favorites, setFavorites] = useState([]);
  const [showFavorites, setShowFavorites] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('electronic');
  const [error, setError] = useState('');
  
  const audioRef = useRef(null);
  const genres = [
    { value: 'electronic', label: 'Electronic' },
    { value: 'techno', label: 'Techno' },
    { value: 'house', label: 'House' },
    { value: 'trance', label: 'Trance' },
    { value: 'dance', label: 'Dance' },
    { value: 'edm', label: 'EDM' }
  ];

  useEffect(() => {
    fetchStations();
    fetchFavorites();
  }, []);

  const fetchStations = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await axios.get(`${API}/stations`);
      setStations(response.data.stations);
    } catch (error) {
      console.error('Error fetching stations:', error);
      setError('Failed to load stations. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStationsByGenre = async (genre) => {
    setIsLoading(true);
    setError('');
    try {
      const response = await axios.get(`${API}/stations/${genre}`);
      setStations(response.data.stations);
    } catch (error) {
      console.error('Error fetching stations by genre:', error);
      setError('Failed to load stations. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const searchStations = async (query) => {
    if (!query.trim()) {
      fetchStations();
      return;
    }
    
    setIsLoading(true);
    setError('');
    try {
      const response = await axios.get(`${API}/search/${encodeURIComponent(query)}`);
      setStations(response.data.stations);
    } catch (error) {
      console.error('Error searching stations:', error);
      setError('Failed to search stations. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchFavorites = async () => {
    try {
      const response = await axios.get(`${API}/favorites`);
      setFavorites(response.data.favorites);
    } catch (error) {
      console.error('Error fetching favorites:', error);
    }
  };

  const playStation = async (station) => {
    try {
      if (currentStation && currentStation.stationuuid === station.stationuuid) {
        // Toggle play/pause for current station
        if (isPlaying) {
          audioRef.current.pause();
          setIsPlaying(false);
        } else {
          audioRef.current.play();
          setIsPlaying(true);
        }
        return;
      }

      // Stop current station if playing
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }

      setCurrentStation(station);
      setIsPlaying(false);
      
      // Load new station
      if (audioRef.current) {
        audioRef.current.src = station.url;
        audioRef.current.volume = volume;
        audioRef.current.load();
        
        try {
          await audioRef.current.play();
          setIsPlaying(true);
        } catch (error) {
          console.error('Error playing station:', error);
          setError('Failed to play station. Please try another one.');
        }
      }
    } catch (error) {
      console.error('Error in playStation:', error);
      setError('Failed to play station. Please try another one.');
    }
  };

  const stopStation = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlaying(false);
    setCurrentStation(null);
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
  };

  const addToFavorites = async (station) => {
    try {
      await axios.post(`${API}/favorites`, {
        stationuuid: station.stationuuid,
        name: station.name,
        url: station.url,
        country: station.country,
        tags: station.tags
      });
      fetchFavorites();
    } catch (error) {
      console.error('Error adding to favorites:', error);
    }
  };

  const removeFromFavorites = async (stationuuid) => {
    try {
      await axios.delete(`${API}/favorites/${stationuuid}`);
      fetchFavorites();
    } catch (error) {
      console.error('Error removing from favorites:', error);
    }
  };

  const isFavorite = (stationuuid) => {
    return favorites.some(fav => fav.stationuuid === stationuuid);
  };

  const handleGenreChange = (genre) => {
    setSelectedGenre(genre);
    setSearchQuery('');
    fetchStationsByGenre(genre);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    searchStations(searchQuery);
  };

  const displayStations = showFavorites ? favorites : stations;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-white mb-2 tracking-wide">
            World Techno Radio
          </h1>
          <p className="text-gray-300 text-lg">
            Stream the best electronic music from around the world
          </p>
        </div>

        {/* Controls */}
        <div className="bg-black bg-opacity-50 rounded-lg p-6 mb-8">
          {/* Genre Selector */}
          <div className="flex flex-wrap gap-2 mb-4">
            {genres.map(genre => (
              <button
                key={genre.value}
                onClick={() => handleGenreChange(genre.value)}
                className={`px-4 py-2 rounded-full transition-all ${
                  selectedGenre === genre.value
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {genre.label}
              </button>
            ))}
          </div>

          {/* Search and Controls */}
          <div className="flex flex-col sm:flex-row gap-4 mb-4">
            <form onSubmit={handleSearch} className="flex-1 flex gap-2">
              <input
                type="text"
                placeholder="Search stations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 px-4 py-2 bg-gray-800 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600"
              />
              <button
                type="submit"
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Search
              </button>
            </form>
            
            <button
              onClick={() => setShowFavorites(!showFavorites)}
              className={`px-6 py-2 rounded-lg transition-colors ${
                showFavorites
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {showFavorites ? 'Show All' : 'Favorites'}
            </button>
          </div>

          {/* Now Playing */}
          {currentStation && (
            <div className="bg-gray-800 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex-1">
                  <h3 className="text-white font-medium">{currentStation.name}</h3>
                  <p className="text-gray-400 text-sm">{currentStation.country}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => playStation(currentStation)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                  >
                    {isPlaying ? 'Pause' : 'Play'}
                  </button>
                  <button
                    onClick={stopStation}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                  >
                    Stop
                  </button>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <span className="text-white text-sm">Volume:</span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={volume}
                  onChange={handleVolumeChange}
                  className="flex-1 accent-purple-600"
                />
                <span className="text-white text-sm">{Math.round(volume * 100)}%</span>
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-600 text-white p-4 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="text-center py-8">
            <div className="text-white text-lg">Loading stations...</div>
          </div>
        )}

        {/* Stations List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayStations.map((station) => (
            <div
              key={station.stationuuid}
              className="bg-black bg-opacity-50 rounded-lg p-6 hover:bg-opacity-70 transition-all cursor-pointer border border-gray-800"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-white font-medium mb-1 line-clamp-2">
                    {station.name}
                  </h3>
                  <p className="text-gray-400 text-sm mb-2">{station.country}</p>
                  <p className="text-gray-500 text-xs mb-2">
                    {station.tags}
                  </p>
                  <p className="text-gray-500 text-xs">
                    {station.bitrate} kbps • {station.codec}
                  </p>
                </div>
                
                <button
                  onClick={() => isFavorite(station.stationuuid) 
                    ? removeFromFavorites(station.stationuuid) 
                    : addToFavorites(station)}
                  className={`ml-2 p-2 rounded-full transition-colors ${
                    isFavorite(station.stationuuid)
                      ? 'text-red-500 hover:text-red-600'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  ♥
                </button>
              </div>
              
              <button
                onClick={() => playStation(station)}
                className={`w-full py-2 rounded-lg transition-colors ${
                  currentStation && currentStation.stationuuid === station.stationuuid
                    ? 'bg-purple-600 text-white hover:bg-purple-700'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {currentStation && currentStation.stationuuid === station.stationuuid
                  ? (isPlaying ? 'Pause' : 'Play')
                  : 'Play'}
              </button>
            </div>
          ))}
        </div>

        {/* No Results */}
        {!isLoading && displayStations.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-400 text-lg">
              {showFavorites ? 'No favorite stations yet' : 'No stations found'}
            </p>
          </div>
        )}

        {/* Audio Element */}
        <audio
          ref={audioRef}
          onEnded={() => setIsPlaying(false)}
          onError={() => {
            setIsPlaying(false);
            setError('Error playing station. Please try another one.');
          }}
          onLoadStart={() => setError('')}
        />
      </div>
    </div>
  );
}

export default App;