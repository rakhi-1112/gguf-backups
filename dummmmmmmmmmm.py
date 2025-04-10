import React, { useEffect, useState } from 'react';
import { BASE_URL } from '../config/api';

const GetNotificationsPage = () => {
  const [notificationData, setNotificationData] = useState([]);
  const [originalNotificationData, setOriginalNotificationData] = useState([]);
  const [notificationIds, setNotificationIds] = useState([]);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [isSortOpen, setIsSortOpen] = useState(false);
  const [filter, setFilter] = useState('');
  const [sort, setSort] = useState('');

  useEffect(() => {
    // Fetch data on mount
    fetch(`${BASE_URL}/get-notifications`)
      .then(res => res.json())
      .then(data => {
        const formattedData = data.result.map(item => ({
          ...item,
          last_modified: new Date(item.last_modified)
        }));
        setNotificationData(formattedData);
        setOriginalNotificationData(formattedData); // Backup for re-filtering
        setNotificationIds(formattedData.map(item => item.nid));
      })
      .catch(err => console.error('Error fetching notifications:', err));
  }, []);

  const toggleFilterDropdown = () => setIsFilterOpen(prev => !prev);
  const toggleSortDropdown = () => setIsSortOpen(prev => !prev);

  const handleFilterSelect = (selectedFilter) => {
    setFilter(selectedFilter);
    applyFilter(selectedFilter);
    setIsFilterOpen(false);
  };

  const applyFilter = (filterType) => {
    const now = new Date();
    const filtered = originalNotificationData.filter(item => {
      const date = new Date(item.last_modified);
      switch (filterType) {
        case 'Today':
          return date.toDateString() === now.toDateString();
        case 'Yesterday':
          const yesterday = new Date();
          yesterday.setDate(now.getDate() - 1);
          return date.toDateString() === yesterday.toDateString();
        case 'Week':
          const weekAgo = new Date();
          weekAgo.setDate(now.getDate() - 7);
          return date >= weekAgo;
        case 'Month':
          const monthAgo = new Date();
          monthAgo.setMonth(now.getMonth() - 1);
          return date >= monthAgo;
        case 'Year':
          const yearAgo = new Date();
          yearAgo.setFullYear(now.getFullYear() - 1);
          return date >= yearAgo;
        default:
          return true;
      }
    });
    setNotificationData(filtered);
    setNotificationIds(filtered.map(item => item.nid));
  };

  const handleSortSelect = (selectedSort) => {
    setSort(selectedSort);
    let sorted = [...notificationData];

    if (selectedSort === 'n_id_ascending') {
      sorted.sort((a, b) => a.nid - b.nid);
    } else if (selectedSort === 'n_id_descending') {
      sorted.sort((a, b) => b.nid - a.nid);
    } else if (selectedSort === 'oldest') {
      sorted.sort((a, b) => a.last_modified - b.last_modified);
    } else if (selectedSort === 'latest') {
      sorted.sort((a, b) => b.last_modified - a.last_modified);
    }

    setNotificationData(sorted);
    setIsSortOpen(false);
  };

  return (
    <div className="p-6">
      <div className="flex gap-4 mb-4">
        {/* Filter Dropdown */}
        <div className="relative">
          <button
            onClick={toggleFilterDropdown}
            className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
          >
            Filter By
          </button>
          {isFilterOpen && (
            <div className="absolute z-10 mt-2 w-48 rounded shadow bg-white ring-1 ring-black ring-opacity-5">
              <div className="py-1 text-left text-sm text-gray-700">
                <button onClick={() => handleFilterSelect('Today')} className="block w-full px-4 py-2 hover:bg-gray-100">Today</button>
                <button onClick={() => handleFilterSelect('Yesterday')} className="block w-full px-4 py-2 hover:bg-gray-100">Yesterday</button>
                <button onClick={() => handleFilterSelect('Week')} className="block w-full px-4 py-2 hover:bg-gray-100">Week</button>
                <button onClick={() => handleFilterSelect('Month')} className="block w-full px-4 py-2 hover:bg-gray-100">Month</button>
                <button onClick={() => handleFilterSelect('Year')} className="block w-full px-4 py-2 hover:bg-gray-100">Year</button>
              </div>
            </div>
          )}
        </div>

        {/* Sort Dropdown */}
        <div className="relative">
          <button
            onClick={toggleSortDropdown}
            className="bg-green-500 text-white py-2 px-4 rounded hover:bg-green-600"
          >
            Sort By
          </button>
          {isSortOpen && (
            <div className="absolute z-10 mt-2 w-48 rounded shadow bg-white ring-1 ring-black ring-opacity-5">
              <div className="py-1 text-left text-sm text-gray-700">
                <button onClick={() => handleSortSelect('n_id_ascending')} className="block w-full px-4 py-2 hover:bg-gray-100">NID Ascending</button>
                <button onClick={() => handleSortSelect('n_id_descending')} className="block w-full px-4 py-2 hover:bg-gray-100">NID Descending</button>
                <button onClick={() => handleSortSelect('oldest')} className="block w-full px-4 py-2 hover:bg-gray-100">Oldest</button>
                <button onClick={() => handleSortSelect('latest')} className="block w-full px-4 py-2 hover:bg-gray-100">Latest</button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Notifications List */}
      <div className="space-y-4">
        {notificationData.length === 0 ? (
          <p>No notifications found.</p>
        ) : (
          notificationData.map((item, index) => (
            <div key={index} className="border p-4 rounded shadow">
              <p><strong>NID:</strong> {item.nid}</p>
              <p><strong>Last Modified:</strong> {item.last_modified.toLocaleString()}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default GetNotificationsPage;
