/**
 * Sistema de Acessibilidade com Leitura de Voz
 * Usa Web Speech API para ler elementos da página
 */
(function() {
    'use strict';

    // Verifica se o navegador suporta Web Speech API
    if (!('speechSynthesis' in window)) {
        return;
    }

    // Estado do sistema de acessibilidade
    const accessibilityState = {
        enabled: false,
        autoReadChat: true,
        speed: 1.0,
        pitch: 1.0,
        volume: 1.0,
        currentUtterance: null,
        isReading: false
    };

    // Elementos do DOM
    const elements = {
        panel: document.getElementById('accessibility-panel'),
        toggle: document.getElementById('accessibility-toggle'),
        menu: document.getElementById('accessibility-menu'),
        closeBtn: document.getElementById('accessibility-close'),
        voiceReaderToggle: document.getElementById('voice-reader-toggle'),
        autoReadChatToggle: document.getElementById('auto-read-chat-toggle'),
        voiceSpeed: document.getElementById('voice-speed'),
        voiceSpeedValue: document.getElementById('voice-speed-value'),
        voicePitch: document.getElementById('voice-pitch'),
        voicePitchValue: document.getElementById('voice-pitch-value'),
        voiceVolume: document.getElementById('voice-volume'),
        voiceVolumeValue: document.getElementById('voice-volume-value'),
        testBtn: document.getElementById('test-voice-btn'),
        stopBtn: document.getElementById('stop-voice-btn')
    };

    // Carrega configurações salvas do localStorage
    function loadSettings() {
        const saved = localStorage.getItem('accessibilitySettings');
        if (saved) {
            try {
                const settings = JSON.parse(saved);
                accessibilityState.enabled = settings.enabled || false;
                accessibilityState.autoReadChat = settings.autoReadChat !== false;
                accessibilityState.speed = settings.speed || 1.0;
                accessibilityState.pitch = settings.pitch || 1.0;
                accessibilityState.volume = settings.volume !== undefined ? settings.volume : 1.0;
                
                // Aplica as configurações aos controles
                if (elements.voiceReaderToggle) {
                    elements.voiceReaderToggle.checked = accessibilityState.enabled;
                }
                if (elements.autoReadChatToggle) {
                    elements.autoReadChatToggle.checked = accessibilityState.autoReadChat;
                }
                if (elements.voiceSpeed) {
                    elements.voiceSpeed.value = accessibilityState.speed;
                    updateSpeedDisplay();
                }
                if (elements.voicePitch) {
                    elements.voicePitch.value = accessibilityState.pitch;
                    updatePitchDisplay();
                }
                if (elements.voiceVolume) {
                    elements.voiceVolume.value = accessibilityState.volume;
                    updateVolumeDisplay();
                }
            } catch (e) {
                // Erro ao carregar configurações - usa padrões
            }
        }
    }

    // Salva configurações no localStorage
    function saveSettings() {
        const settings = {
            enabled: accessibilityState.enabled,
            autoReadChat: accessibilityState.autoReadChat,
            speed: accessibilityState.speed,
            pitch: accessibilityState.pitch,
            volume: accessibilityState.volume
        };
        localStorage.setItem('accessibilitySettings', JSON.stringify(settings));
    }

    // Atualiza display dos valores
    function updateSpeedDisplay() {
        if (elements.voiceSpeedValue) {
            elements.voiceSpeedValue.textContent = accessibilityState.speed.toFixed(1) + 'x';
        }
    }

    function updatePitchDisplay() {
        if (elements.voicePitchValue) {
            elements.voicePitchValue.textContent = accessibilityState.pitch.toFixed(1);
        }
    }

    function updateVolumeDisplay() {
        if (elements.voiceVolumeValue) {
            elements.voiceVolumeValue.textContent = Math.round(accessibilityState.volume * 100) + '%';
        }
    }

    // Para a leitura atual
    function stopReading() {
        if (accessibilityState.isReading) {
            window.speechSynthesis.cancel();
            accessibilityState.currentUtterance = null;
            accessibilityState.isReading = false;
        }
    }

    // Lê um texto usando Web Speech API
    function readText(text, options = {}) {
        if (!accessibilityState.enabled || !text || typeof text !== 'string') {
            return;
        }

        // Para leitura anterior se houver
        stopReading();

        // Remove HTML tags e limpa o texto
        const cleanText = text
            .replace(/<[^>]*>/g, '') // Remove tags HTML
            .replace(/&nbsp;/g, ' ')
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'")
            .trim();

        if (!cleanText) return;

        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        // Configurações da voz
        utterance.rate = options.speed || accessibilityState.speed;
        utterance.pitch = options.pitch || accessibilityState.pitch;
        utterance.volume = options.volume !== undefined ? options.volume : accessibilityState.volume;
        
        // Tenta usar voz em português
        const voices = window.speechSynthesis.getVoices();
        const portugueseVoice = voices.find(voice => 
            voice.lang.includes('pt') || voice.lang.includes('PT')
        );
        if (portugueseVoice) {
            utterance.voice = portugueseVoice;
            utterance.lang = portugueseVoice.lang;
        } else {
            utterance.lang = 'pt-BR';
        }

        // Eventos
        utterance.onstart = () => {
            accessibilityState.isReading = true;
            accessibilityState.currentUtterance = utterance;
        };

        utterance.onend = () => {
            accessibilityState.isReading = false;
            accessibilityState.currentUtterance = null;
        };

        utterance.onerror = (error) => {
            // Silenciosamente trata erros de síntese de voz
            // Alguns navegadores podem ter problemas com certas vozes ou textos
            accessibilityState.isReading = false;
            accessibilityState.currentUtterance = null;
            
            // Tenta novamente com configurações mais simples se houver erro
            if (error.error === 'synthesis-failed' || error.error === 'synthesis-unavailable') {
                // Não tenta novamente automaticamente para evitar loops
                return;
            }
        };

        // Aguarda vozes carregarem se necessário
        if (voices.length === 0) {
            const voicesHandler = () => {
                const updatedVoices = window.speechSynthesis.getVoices();
                if (updatedVoices.length > 0) {
                    const ptVoice = updatedVoices.find(voice => 
                        voice.lang.includes('pt') || voice.lang.includes('PT')
                    );
                    if (ptVoice) {
                        utterance.voice = ptVoice;
                        utterance.lang = ptVoice.lang;
                    }
                    // Remove o listener após usar
                    window.speechSynthesis.removeEventListener('voiceschanged', voicesHandler);
                    // Verifica se a síntese está disponível antes de falar
                    if (window.speechSynthesis.speaking === false) {
                        try {
                            window.speechSynthesis.speak(utterance);
                        } catch (e) {
                            // Erro silencioso - síntese pode não estar disponível
                        }
                    }
                }
            };
            window.speechSynthesis.addEventListener('voiceschanged', voicesHandler);
            // Timeout de segurança caso as vozes não carreguem
            setTimeout(() => {
                window.speechSynthesis.removeEventListener('voiceschanged', voicesHandler);
                if (window.speechSynthesis.speaking === false && !accessibilityState.isReading) {
                    try {
                        window.speechSynthesis.speak(utterance);
                    } catch (e) {
                        // Erro silencioso
                    }
                }
            }, 1000);
        } else {
            // Verifica se a síntese está disponível antes de falar
            if (window.speechSynthesis.speaking === false) {
                try {
                    window.speechSynthesis.speak(utterance);
                } catch (e) {
                    // Erro silencioso - síntese pode não estar disponível
                }
            }
        }
    }

    // Lê mensagens do chat automaticamente
    function readChatMessage(messageElement) {
        if (!accessibilityState.enabled || !accessibilityState.autoReadChat) {
            return;
        }

        // Extrai o texto da mensagem
        let text = '';
        
        // Remove imagens e formatação, mantém apenas o texto
        const clone = messageElement.cloneNode(true);
        const images = clone.querySelectorAll('img');
        images.forEach(img => img.remove());
        
        // Remove tags strong mas mantém o texto
        const strongs = clone.querySelectorAll('strong');
        strongs.forEach(strong => {
            const textNode = document.createTextNode(strong.textContent + ': ');
            strong.parentNode.replaceChild(textNode, strong);
        });
        
        text = clone.textContent || clone.innerText || '';
        
        // Limpa o texto
        text = text
            .replace(/\s+/g, ' ')
            .replace(/InvestiChat:/g, 'InvestiChat diz:')
            .replace(/Você:/g, 'Você disse:')
            .trim();

        if (text) {
            readText(text);
        }
    }

    // Observa novas mensagens no chat
    function observeChatMessages() {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;

        // Observer para novas mensagens
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) { // Element node
                        // Verifica se é uma mensagem do chat
                        if (node.classList && (
                            node.classList.contains('message') ||
                            node.classList.contains('bot-message') ||
                            node.classList.contains('user-message')
                        )) {
                            // Aguarda um pouco para garantir que o conteúdo foi renderizado
                            setTimeout(() => {
                                readChatMessage(node);
                            }, 300);
                        }
                    }
                });
            });
        });

        observer.observe(chatContainer, {
            childList: true,
            subtree: true
        });
    }

    // Inicializa o sistema
    function init() {
        // Verifica se os elementos existem
        if (!elements.panel) {
            return;
        }

        if (!elements.toggle) {
            return;
        }

        if (!elements.menu) {
            return;
        }

        loadSettings();

        // Toggle do menu
        if (elements.toggle) {
            elements.toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (elements.menu) {
                    const currentDisplay = window.getComputedStyle(elements.menu).display;
                    const isVisible = currentDisplay !== 'none';
                    elements.menu.style.display = isVisible ? 'none' : 'block';
                    elements.menu.setAttribute('aria-hidden', isVisible ? 'true' : 'false');
                }
            });
        }

        // Fechar menu
        if (elements.closeBtn) {
            elements.closeBtn.addEventListener('click', () => {
                if (elements.menu) {
                    elements.menu.style.display = 'none';
                    elements.menu.setAttribute('aria-hidden', 'true');
                }
            });
        }

        // Toggle leitura de voz
        if (elements.voiceReaderToggle) {
            elements.voiceReaderToggle.addEventListener('change', (e) => {
                accessibilityState.enabled = e.target.checked;
                saveSettings();
                if (!accessibilityState.enabled) {
                    stopReading();
                }
            });
        }

        // Toggle leitura automática do chat
        if (elements.autoReadChatToggle) {
            elements.autoReadChatToggle.addEventListener('change', (e) => {
                accessibilityState.autoReadChat = e.target.checked;
                saveSettings();
            });
        }

        // Controles de velocidade
        if (elements.voiceSpeed) {
            elements.voiceSpeed.addEventListener('input', (e) => {
                accessibilityState.speed = parseFloat(e.target.value);
                updateSpeedDisplay();
                saveSettings();
            });
        }

        // Controles de tom
        if (elements.voicePitch) {
            elements.voicePitch.addEventListener('input', (e) => {
                accessibilityState.pitch = parseFloat(e.target.value);
                updatePitchDisplay();
                saveSettings();
            });
        }

        // Controles de volume
        if (elements.voiceVolume) {
            elements.voiceVolume.addEventListener('input', (e) => {
                accessibilityState.volume = parseFloat(e.target.value);
                updateVolumeDisplay();
                saveSettings();
            });
        }

        // Botão de teste
        if (elements.testBtn) {
            elements.testBtn.addEventListener('click', () => {
                readText('Este é um teste do sistema de leitura de voz. Se você está ouvindo esta mensagem, o sistema está funcionando corretamente.');
            });
        }

        // Botão de parar
        if (elements.stopBtn) {
            elements.stopBtn.addEventListener('click', () => {
                stopReading();
            });
        }

        // Observa mensagens do chat
        observeChatMessages();

        // Carrega vozes quando disponíveis
        if (window.speechSynthesis.getVoices().length === 0) {
            window.speechSynthesis.onvoiceschanged = () => {
                // Vozes carregadas
            };
        }
    }

    // Exporta funções para uso externo
    window.AccessibilityReader = {
        read: readText,
        stop: stopReading,
        isEnabled: () => accessibilityState.enabled,
        setEnabled: (enabled) => {
            accessibilityState.enabled = enabled;
            if (elements.voiceReaderToggle) {
                elements.voiceReaderToggle.checked = enabled;
            }
            saveSettings();
            if (!enabled) {
                stopReading();
            }
        }
    };

    // Inicializa quando o DOM estiver pronto
    function startInit() {
        try {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    setTimeout(init, 200);
                });
            } else {
                // Aguarda um pouco para garantir que todos os elementos foram renderizados
                setTimeout(init, 200);
            }
        } catch (error) {
            // Erro silencioso na inicialização
        }
    }

    startInit();
})();

