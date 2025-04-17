document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    // Configuración del webhook de n8n
    const N8N_WEBHOOK_URL = 'http://recruiter-dev-n8n:5678/ask';
    
    // Manejar el envío de mensajes
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;
        
        // Mostrar mensaje del usuario
        addMessageToChat(message, 'user');
        userInput.value = '';
        
        // Enviar al webhook de n8n
        fetch(N8N_WEBHOOK_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Basic ' + btoa('admin:admin') // Autenticación básica
            },
            body: JSON.stringify({ query: message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            return response.json();
        })
        .then(data => {
            // Mostrar respuesta del asistente
            if (data.response) {
                addMessageToChat(data.response, 'bot');
            } else {
                addMessageToChat("Lo siento, no pude obtener una respuesta. Intenta con otra pregunta.", 'bot');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            addMessageToChat("Hubo un error al comunicarme con el servidor. Por favor intenta más tarde.", 'bot');
        });
    }
    
    // Añadir mensaje al chat
    function addMessageToChat(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', `${sender}-message`);
        
        // Si el mensaje es un array (como lista de libros o noticias), formatearlo
        if (Array.isArray(message)) {
            const list = document.createElement('ul');
            message.forEach(item => {
                const li = document.createElement('li');
                
                if (item.title && item.price) { // Es un libro
                    li.innerHTML = `<strong>${item.title}</strong> - £${item.price}<br>
                                    <small>Categoría: ${item.category}</small>`;
                    if (item.image_url) {
                        li.innerHTML += `<br><img src="${item.image_url}" alt="Portada" style="max-width: 100px;">`;
                    }
                } else if (item.title && item.url) { // Es una noticia
                    li.innerHTML = `<a href="${item.url}" target="_blank">${item.title}</a>`;
                    if (item.score) {
                        li.innerHTML += `<br><small>Puntos: ${item.score}</small>`;
                    }
                } else {
                    li.textContent = JSON.stringify(item);
                }
                
                list.appendChild(li);
            });
            messageDiv.appendChild(list);
        } else if (typeof message === 'object') { // Objeto no array
            messageDiv.textContent = JSON.stringify(message);
        } else { // Texto plano
            messageDiv.innerHTML = `<p>${message}</p>`;
        }
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});