const API_URL = ''; // Proxied by Vite

const handleResponse = async (response) => {
    if (!response.ok) {
        let errorMessage = 'An error occurred';
        try {
            const error = await response.json();
            errorMessage = error.detail || errorMessage;
        } catch (e) {
            // response was not json
        }
        const error = new Error(errorMessage);
        error.status = response.status;
        throw error;
    }
    return response.json();
};

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
        return handleResponse(response);
    },

    getVectors: async (token) => {
        const response = await fetch(`${API_URL}/list_vectorDBs/`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return handleResponse(response);
    },

    createDB: async (token) => {
        const response = await fetch(`${API_URL}/create_vectorDB/`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` }
        });
        return handleResponse(response);
    },

    deleteDB: async (token, dbHash) => {
        const response = await fetch(`${API_URL}/delete_vectorDB/?db_hash=${dbHash}`, {
            method: 'DELETE',
            headers: { Authorization: `Bearer ${token}` }
        });
        return handleResponse(response);
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
        return handleResponse(response);
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
        return handleResponse(response);
    }
};
