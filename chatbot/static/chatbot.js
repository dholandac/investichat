/*
 * Este arquivo contém apenas a lógica que DEVE estar no cliente:
 * - Interações em tempo real
 * - Manipulação de DOM essencial
 * - Eventos do usuário
 * 
 * Toda formatação, validação e renderização inicial é feita no Django.
*/

(function() {
    'use strict';

    // ========================================
    // CONFIGURAÇÃO E ELEMENTOS
    // ========================================
    const elements = {
        chatMessages: document.getElementById('chat-messages'),
        userInput: document.getElementById('user-input'),
        sendButton: document.getElementById('send-button'),
        dropdownSelected: document.getElementById('dropdown-selected'),
        dropdownList: document.getElementById('dropdown-list'),
        customDropdown: document.getElementById('custom-dropdown'),
        questionnaireForm: document.getElementById('questionarioForm'),
        investmentData: document.getElementById('investment-data'),
    };

    // CSRF Token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    // ID da conversa atual
    let conversationId = elements.chatMessages?.dataset?.conversationId 
        ? parseInt(elements.chatMessages.dataset.conversationId) 
        : null;

    // ========================================
    // NOTIFICAÇÕES TOAST
    // ========================================
    
    function showNotification(message, type = 'error') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `notification-toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Remove após 3 segundos
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ========================================
    // CHAT: FUNÇÕES PRINCIPAIS
    // ========================================
    
    function scrollChatToBottom() {
        if (!elements.chatMessages) return;
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }

    function addMessage(content, isUser = false) {
        if (!elements.chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
        messageDiv.classList.add('message-appear');
        
        if (isUser) {
            messageDiv.style.cssText = 'background-color:#e3f2fd; text-align:right; margin-bottom:10px; padding:8px;';
            messageDiv.innerHTML = `<strong>Você:</strong> ${content}`;
        } else {
            messageDiv.style.cssText = 'background-color:#f1f8e9; margin-bottom:10px; padding:8px;';
            const formatted = content
                .replace(/\r\n/g, '\n')
                .replace(/\n{2,}/g, '</p><p>')
                .replace(/\n/g, '<br>');
            messageDiv.innerHTML = `<img width="35" height="35" style="vertical-align: middle; margin-right: 8px; margin-bottom: 7px" src="/static/images/bot.png"><strong>InvestiChat:</strong><br><p>${formatted}</p>`;
        }
        
        elements.chatMessages.appendChild(messageDiv);
        scrollChatToBottom();
    }

    function showBotLoading() {
        if (document.getElementById('bot-loading-msg')) return;
        
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot-message';
        loadingDiv.id = 'bot-loading-msg';
        loadingDiv.innerHTML = `<img width="35" height="35" style="vertical-align: middle; margin-right: 8px; margin-bottom: 7px" src="/static/images/bot.png"><strong>InvestiChat:</strong><br><img src="/static/images/loading.svg" alt="Carregando..." style="width:32px;vertical-align:middle;"> <span style="color:#888;">Escrevendo...</span>`;
        
        elements.chatMessages.appendChild(loadingDiv);
        scrollChatToBottom();
    }

    function removeBotLoading() {
        document.getElementById('bot-loading-msg')?.remove();
    }

    async function sendMessage() {
        const message = elements.userInput.value.trim();
        if (!message) return;

        addMessage(message, true);
        elements.userInput.value = '';
        elements.sendButton.disabled = true;
        showBotLoading();

        try {
            const response = await fetch('/chatbot/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ 
                    message: message, 
                    conversation_id: conversationId 
                })
            });

            const data = await response.json();
            removeBotLoading();

            if (data.status === 'success') {
                addMessage(data.response);
                if (data.conversation_id) {
                    conversationId = data.conversation_id;
                    if (elements.chatMessages) {
                        elements.chatMessages.dataset.conversationId = conversationId;
                    }
                }
            } else {
                // Mostra notificação ao invés de adicionar ao chat
                showNotification(data.error || 'Erro ao processar mensagem', 'error');
            }
        } catch (error) {
            removeBotLoading();
            console.error('Erro:', error);
            // Mostra notificação ao invés de adicionar ao chat
            showNotification('Erro de conexão. Tente novamente.', 'error');
        } finally {
            elements.sendButton.disabled = false;
        }
    }


    // ========================================
    // DROPDOWN: SELEÇÃO DE AÇÕES
    // ========================================
    
    function getSelectedStocks() {
        const checkboxes = document.querySelectorAll('#dropdown-list input[type=checkbox]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    async function saveStockSelection(stocks) {
        try {
            await fetch('/chatbot/save-stock-selection/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ stocks })
            });
        } catch (error) {
            console.error('Erro ao salvar seleção:', error);
        }
    }

    async function refreshInvestmentData() {
        if (!elements.investmentData) return;

        const selectedStocks = getSelectedStocks();
        if (selectedStocks.length === 0) {
            elements.investmentData.innerHTML = '<div class="error">Selecione pelo menos uma ação.</div>';
            return;
        }

        const hadContent = elements.investmentData.innerHTML.trim().length > 0;
        const lastUpdatedElement = elements.investmentData.querySelector('.last-updated');
        const previousLastUpdatedText = lastUpdatedElement ? lastUpdatedElement.textContent : null;

        if (hadContent && lastUpdatedElement) {
            lastUpdatedElement.textContent = 'Atualizando dados de investimento...';
        } else if (!hadContent) {
            elements.investmentData.innerHTML = '<div class="loading">Carregando dados de investimento...</div>';
        }

        let updateSucceeded = false;

        try {
            // Faz requisição para obter dados atualizados
            const response = await fetch('/chatbot/refresh-investment/', {
                headers: {
                    'HX-Request': 'true'  // Simula requisição HTMX para receber HTML
                }
            });
            
            if (response.ok) {
                const html = await response.text();
                elements.investmentData.innerHTML = html;
                updateSucceeded = true;
            } else {
                throw new Error('Erro na requisição');
            }
        } catch (error) {
            console.error('Erro ao atualizar investimentos:', error);
            if (hadContent) {
                showNotification('Erro ao atualizar dados de investimento.', 'error');
            } else {
                elements.investmentData.innerHTML = '<div class="error">Erro ao carregar dados.</div>';
            }
        } finally {
            if (!updateSucceeded && hadContent && lastUpdatedElement && previousLastUpdatedText !== null) {
                lastUpdatedElement.textContent = previousLastUpdatedText;
            }
        }
    }

    function setupDropdown() {
        if (!elements.customDropdown) return;

        // Toggle dropdown
        elements.dropdownSelected?.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = elements.dropdownList.style.display === 'block';
            elements.dropdownList.style.display = isVisible ? 'none' : 'block';
        });

        // Fechar ao clicar fora
        document.addEventListener('click', (e) => {
            if (!elements.customDropdown.contains(e.target)) {
                elements.dropdownList.style.display = 'none';
            }
        });

        // Limitar seleção e atualizar
        elements.dropdownList?.addEventListener('change', async (e) => {
            if (e.target.type !== 'checkbox') return;

            const checked = document.querySelectorAll('#dropdown-list input[type=checkbox]:checked');
            
            if (checked.length > 3) {
                e.target.checked = false;
                alert('Selecione no máximo 3 ações.');
            } else {
                const selected = getSelectedStocks();
                // Aguarda salvar antes de atualizar
                await saveStockSelection(selected);
                await refreshInvestmentData();
            }
        });
    }

    // ========================================
    // QUESTIONÁRIO: VALIDAÇÃO E ENVIO
    // ========================================
    
    function setupQuestionnaire() {
        if (!elements.questionnaireForm) return;

        elements.questionnaireForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(elements.questionnaireForm);
            const errorMessage = document.getElementById('errorMessage');
            
            // Valida que todas as perguntas foram respondidas
            let allAnswered = true;
            for (let i = 1; i <= 10; i++) {
                if (!formData.has(`pergunta_${i}`)) {
                    allAnswered = false;
                    break;
                }
            }
            
            if (!allAnswered) {
                errorMessage.style.display = 'block';
                return;
            }
            
            errorMessage.style.display = 'none';
            
            try {
                const response = await fetch(elements.questionnaireForm.action, {
                    method: 'POST',
                    body: new URLSearchParams(formData),
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('questionnaireModal').style.display = 'none';
                    window.location.reload();
                } else {
                    alert('Erro ao salvar o perfil: ' + data.error);
                }
            } catch (error) {
                console.error('Erro:', error);
                alert('Ocorreu um erro ao enviar o questionário.');
            }
        });
    }

    // ========================================
    // INICIALIZAÇÃO
    // ========================================
    
    async function loadSavedStockSelection() {
        try {
            const response = await fetch('/chatbot/get-stock-selection/');
            const data = await response.json();
            
            if (data.stocks && Array.isArray(data.stocks)) {
                // Desmarcar todos os checkboxes
                document.querySelectorAll('#dropdown-list input[type=checkbox]').forEach(cb => {
                    cb.checked = false;
                });
                
                // Marcar apenas as ações salvas
                data.stocks.forEach(symbol => {
                    const checkbox = document.querySelector(`#dropdown-list input[type=checkbox][value="${symbol}"]`);
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                });
                
                // Atualizar dados de investimento
                await refreshInvestmentData();
            }
        } catch (error) {
            console.error('Erro ao carregar seleção de ações:', error);
            // Se falhar, tenta atualizar com as ações padrão
            await refreshInvestmentData();
        }
    }
    
    function init() {
        // Estiliza ícone do menu
        const menuIcon = document.getElementById('menu-icon');
        if (menuIcon) {
            menuIcon.style.filter = 'invert(1) brightness(100)';
        }

        // Event listeners do chat
        elements.sendButton?.addEventListener('click', sendMessage);
        elements.userInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Setup de componentes
        setupDropdown();
        setupQuestionnaire();

        // Scroll inicial do chat
        requestAnimationFrame(scrollChatToBottom);
        window.addEventListener('load', scrollChatToBottom);

        // Carrega seleção de ações salva e depois atualiza automaticamente
        loadSavedStockSelection().then(() => {
            // Atualização automática de investimentos a cada 30s
            setInterval(refreshInvestmentData, 30000);
        });
    }

    // Aguarda DOM estar pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
