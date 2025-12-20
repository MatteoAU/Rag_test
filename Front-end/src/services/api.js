const API_URL = ''; // Proxied by Vite

export const api = {
    login: async (username, password) => {
        // Note: Backend endpoint is /token/ (trailing slash might be needed)
        // Checking controller, it is @app.post("/token/")
        const response = await fetch(`${API_URL}/token/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }
        return response.json();
    },

    getVectors: async (token) => {
        const response = await fetch(`${API_URL}/list_vectorDBs/`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch DBs');
        return response.json();
    },

    createDB: async (token) => {
        const response = await fetch(`${API_URL}/create_vectorDB/`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to create DB');
        return response.json();
    },

    deleteDB: async (token, dbHash) => {
        const response = await fetch(`${API_URL}/delete_vectorDB/?db_hash=${dbHash}`, {
            method: 'DELETE',
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to delete DB');
        return response.json();
    },

    uploadFile: async (token, dbHash, file) => {
        const formData = new FormData();
        formData.append('db_hash', dbHash);
        formData.append('file', file);

        const response = await fetch(`${API_URL}/upload_file/`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
            body: formData
        });
        if (!response.ok) throw new Error('Upload failed');
        return response.json();
    },

    query: async (token, dbHash, queryText) => {
        const formData = new FormData();
        formData.append('db_hash', dbHash);
        formData.append('query', queryText);
        formData.append('top_k', 5);

        const response = await fetch(`${API_URL}/query/`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
            body: formData
        });
        if (!response.ok) throw new Error('Query failed');
        return response.json();
    }
};
