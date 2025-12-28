/**
 * Frontend JavaScript for Music Recommendation Agent
 */

// DOM Elements
const form = document.getElementById('recommendationForm');
const submitBtn = document.getElementById('submitBtn');
const submitText = document.getElementById('submitText');
const submitLoader = document.getElementById('submitLoader');
const errorMessage = document.getElementById('errorMessage');
const recommendationsDiv = document.getElementById('recommendations');
const recommendationsList = document.getElementById('recommendationsList');
const detectLocationBtn = document.getElementById('detectLocation');
const locationInput = document.getElementById('location');

// Detect location button handler
detectLocationBtn.addEventListener('click', async () => {
    if (!navigator.geolocation) {
        showError('Geolocation is not supported by your browser.');
        return;
    }

    detectLocationBtn.disabled = true;
    detectLocationBtn.textContent = 'Detecting...';

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            try {
                const { latitude, longitude } = position.coords;
                // Use reverse geocoding API (free service)
                const response = await fetch(
                    `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`
                );
                const data = await response.json();
                
                if (data.address) {
                    const city = data.address.city || data.address.town || data.address.village || '';
                    const country = data.address.country || '';
                    locationInput.value = city && country ? `${city}, ${country}` : country || 'Location detected';
                } else {
                    locationInput.value = `${latitude}, ${longitude}`;
                }
            } catch (error) {
                console.error('Error getting location name:', error);
                locationInput.value = 'Location detected';
            } finally {
                detectLocationBtn.disabled = false;
                detectLocationBtn.textContent = 'Detect My Location';
            }
        },
        (error) => {
            showError('Unable to detect your location. Please enter it manually.');
            detectLocationBtn.disabled = false;
            detectLocationBtn.textContent = 'Detect My Location';
        }
    );
});

// Form submission handler
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Hide previous results and errors
    hideError();
    recommendationsDiv.style.display = 'none';
    
    // Get form data
    const formData = {
        mood: document.getElementById('mood').value.trim(),
        activity: document.getElementById('activity').value.trim(),
        location: locationInput.value.trim(),
        tags: document.getElementById('tags').value.trim()
    };
    
    // Validate required fields
    if (!formData.mood || !formData.activity) {
        showError('Please fill in both mood and activity fields.');
        return;
    }
    
    // Show loading state
    setLoading(true);
    
    // Start refreshing logs if logs section is visible
    if (logsContainer.style.display !== 'none') {
        startLogsRefresh();
    }
    
    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to get recommendations');
        }
        
        // Display recommendations
        displayRecommendations(data.recommendations || []);
        
        // Load recent memories
        loadRecentMemories();
        
        // Refresh logs to show the processing steps
        if (logsContainer.style.display !== 'none') {
            loadLogs();
        }
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An error occurred while getting recommendations. Make sure the Python API server is running on port 5001.');
    } finally {
        setLoading(false);
    }
});

function setLoading(loading) {
    submitBtn.disabled = loading;
    submitText.style.display = loading ? 'none' : 'inline';
    submitLoader.style.display = loading ? 'inline-block' : 'none';
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

function hideError() {
    errorMessage.style.display = 'none';
}

function displayRecommendations(recommendations) {
    if (!recommendations || recommendations.length === 0) {
        recommendationsList.innerHTML = '<p>No recommendations available.</p>';
        recommendationsDiv.style.display = 'block';
        return;
    }
    
    recommendationsList.innerHTML = recommendations.map((rec, index) => {
        const song = rec.song || 'Unknown Song';
        const artist = rec.artist || 'Unknown Artist';
        const genre = rec.genre || 'Unknown';
        const energyLevel = rec.energy_level || 'Unknown';
        const reason = rec.reason || 'No reason provided';
        
        const youtubeQuery = encodeURIComponent(`${song} ${artist}`);
        const youtubeUrl = `https://www.youtube.com/results?search_query=${youtubeQuery}`;
        
        return `
            <div class="recommendation-card">
                <h3>${song}</h3>
                <div class="artist">by ${artist}</div>
                <div class="details">
                    <span class="detail-item"><strong>Genre:</strong> ${genre}</span>
                    <span class="detail-item"><strong>Energy:</strong> ${energyLevel}</span>
                </div>
                <div class="reason">${reason}</div>
                <a href="${youtubeUrl}" target="_blank" class="youtube-link">
                    🎵 Listen on YouTube
                </a>
            </div>
        `;
    }).join('');
    
    recommendationsDiv.style.display = 'block';
}

async function loadRecentMemories() {
    try {
        const response = await fetch('/api/memory/recent?limit=5');
        const data = await response.json();
        
        if (data.memories && data.memories.length > 0) {
            const memoriesDiv = document.getElementById('recentMemories');
            const memoriesList = document.getElementById('memoriesList');
            
            memoriesList.innerHTML = data.memories.map(mem => {
                const content = mem.content || 'No content';
                const timestamp = mem.created_at ? new Date(mem.created_at).toLocaleString() : '';
                return `
                    <div class="memory-item">
                        <strong>${timestamp}</strong><br>
                        ${content}
                    </div>
                `;
            }).join('');
            
            memoriesDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading memories:', error);
        // Don't show error for memories, it's optional
    }
}

// Load recent memories on page load
loadRecentMemories();

// Logs functionality
let logsAutoRefresh = true;
let logsAutoScroll = true;
let logsRefreshInterval = null;

const logsContainer = document.getElementById('logsContainer');
const logsList = document.getElementById('logsList');
const toggleLogsBtn = document.getElementById('toggleLogs');
const clearLogsBtn = document.getElementById('clearLogs');
const autoScrollBtn = document.getElementById('autoScroll');

// Toggle logs visibility
toggleLogsBtn.addEventListener('click', () => {
    const isVisible = logsContainer.style.display !== 'none';
    logsContainer.style.display = isVisible ? 'none' : 'block';
    toggleLogsBtn.textContent = isVisible ? 'Show Logs' : 'Hide Logs';
    
    if (!isVisible) {
        loadLogs();
        startLogsRefresh();
    } else {
        stopLogsRefresh();
    }
});

// Clear logs
clearLogsBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to clear all logs?')) {
        try {
            await fetch('/api/logs/clear', { method: 'POST' });
            logsList.innerHTML = '';
            loadLogs();
        } catch (error) {
            console.error('Error clearing logs:', error);
        }
    }
});

// Toggle auto-scroll
autoScrollBtn.addEventListener('click', () => {
    logsAutoScroll = !logsAutoScroll;
    autoScrollBtn.classList.toggle('active', logsAutoScroll);
    if (logsAutoScroll) {
        scrollToBottom();
    }
});

function startLogsRefresh() {
    if (logsRefreshInterval) return;
    logsRefreshInterval = setInterval(() => {
        if (logsAutoRefresh && logsContainer.style.display !== 'none') {
            loadLogs(true); // silent update
        }
    }, 1000); // Refresh every second
}

function stopLogsRefresh() {
    if (logsRefreshInterval) {
        clearInterval(logsRefreshInterval);
        logsRefreshInterval = null;
    }
}

async function loadLogs(silent = false) {
    try {
        const response = await fetch('/api/logs?limit=100');
        const data = await response.json();
        
        if (data.logs) {
            const wasAtBottom = isScrolledToBottom();
            
            logsList.innerHTML = data.logs.map(log => {
                const levelClass = log.level || 'INFO';
                const timestamp = log.timestamp || '';
                const message = log.message || '';
                const dataStr = log.data && Object.keys(log.data).length > 0 
                    ? JSON.stringify(log.data, null, 2) 
                    : '';
                
                return `
                    <div class="log-entry ${levelClass}">
                        <span class="log-timestamp">${timestamp}</span>
                        <span class="log-level">[${levelClass}]</span>
                        <span class="log-message">${escapeHtml(message)}</span>
                        ${dataStr ? `<div class="log-data">${escapeHtml(dataStr)}</div>` : ''}
                    </div>
                `;
            }).join('');
            
            if (logsAutoScroll && (wasAtBottom || !silent)) {
                scrollToBottom();
            }
        }
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

function scrollToBottom() {
    if (logsContainer) {
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }
}

function isScrolledToBottom() {
    if (!logsContainer) return true;
    const threshold = 50;
    return logsContainer.scrollHeight - logsContainer.scrollTop - logsContainer.clientHeight < threshold;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Start loading logs if visible on page load
if (logsContainer.style.display !== 'none') {
    loadLogs();
    startLogsRefresh();
}

