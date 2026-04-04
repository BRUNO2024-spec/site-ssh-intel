document.addEventListener('DOMContentLoaded', () => {
    const successModal = document.getElementById('success-modal');
    const copyAllBtn = document.getElementById('copy-all-btn');
    const MAX_CAPACITY = 200;

    // --- Universal Modal Management ---
    const closeAllModals = () => {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    };

    // Close on click outside or ESC key
    window.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });

    window.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') closeAllModals();
    });

    // Close buttons event listeners
    document.getElementById('closeXrayModal')?.addEventListener('click', closeAllModals);
    document.getElementById('btnFooterCloseXray')?.addEventListener('click', closeAllModals);
    document.getElementById('closeSuccessModal')?.addEventListener('click', closeAllModals);
    document.querySelector('#success-modal .btn-secondary')?.addEventListener('click', closeAllModals);

    // --- XRAY Links Functionality ---
    const xrayModal = document.getElementById('xray-modal');
    const xrayBtn = document.getElementById('xrayLinksBtn');
    const xrayList = document.getElementById('xray-links-list');
    const uuidInput = document.getElementById('user-xray-uuid');
    const uuidError = document.getElementById('uuid-error');
    
    let rawXrayLinks = []; // Store templates from API

    const validateUUID = (uuid) => {
        const regex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        return regex.test(uuid);
    };

    const renderXrayLinks = () => {
        const uuid = uuidInput.value.trim();
        const isValid = validateUUID(uuid);

        if (uuid && !isValid) {
            uuidError.style.display = 'block';
            uuidInput.style.borderColor = 'var(--danger)';
        } else {
            uuidError.style.display = 'none';
            uuidInput.style.borderColor = uuid ? 'var(--primary)' : 'var(--border)';
        }

        xrayList.innerHTML = rawXrayLinks.map(link => {
            const finalLink = uuid ? link.link.replace(/{uuid}/g, uuid) : link.link;
            const isPlaceholder = finalLink.includes('{uuid}');
            
            return `
                <div class="xray-link-item">
                    <label style="display: block; font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.5rem;">${link.name}</label>
                    <div class="copy-box" style="margin-bottom: 0; ${!isValid && uuid ? 'opacity: 0.5; pointer-events: none;' : ''}">
                        <span id="xray-l-${link.id}" style="font-size: 0.8rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 250px;">${finalLink}</span>
                        <button onclick="copyXrayLink('${link.id}', '${finalLink.replace(/'/g, "\\'")}')" ${!isValid && uuid ? 'disabled' : ''}>
                            <i class="far fa-copy"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    };

    window.copyXrayLink = (id, text) => {
        if (text.includes('{uuid}')) {
            showToast('Por favor, insira seu UUID primeiro.', 'error');
            uuidInput.focus();
            return;
        }
        copyToClipboardUniversal(text).then(() => {
            showToast('Link XRAY copiado!');
        });
    };

    if (xrayBtn) {
        xrayBtn.addEventListener('click', async () => {
            xrayModal.style.display = 'flex';
            
            // Load saved UUID
            const savedUUID = localStorage.getItem('xray_uuid');
            if (savedUUID) uuidInput.value = savedUUID;
            
            uuidInput.focus();
            xrayList.innerHTML = '<div class="text-center py-4 text-muted">Carregando...</div>';
            
            try {
                const response = await fetch('/api/xray-links');
                rawXrayLinks = await response.json();
                
                if (rawXrayLinks.length === 0) {
                    xrayList.innerHTML = '<div class="text-center py-4 text-muted italic">Nenhum link disponível.</div>';
                    return;
                }

                renderXrayLinks();
            } catch (error) {
                xrayList.innerHTML = '<div class="text-center py-4 text-danger">Erro ao carregar links.</div>';
            }
        });
    }

    uuidInput?.addEventListener('input', () => {
        const val = uuidInput.value.trim();
        if (validateUUID(val)) localStorage.setItem('xray_uuid', val);
        renderXrayLinks();
    });

    // --- Monitoring Online Users (Multiple Cards) ---
    const updateAllCards = async () => {
        try {
            const response = await fetch('/online/all');
            const data = await response.json();

            document.querySelectorAll('.server-card').forEach((card) => {
                const cardId = card.getAttribute('data-card-id');
                const result = data[cardId] || { online: 0, status: 'Offline' };
                
                const onlineCountEl = card.querySelector('.online-users-count');
                const statusTextEl = card.querySelector('.server-status-text');
                const dotEl = card.querySelector('.dot');
                const createBtn = card.querySelector('.create-btn');
                const btnText = createBtn ? createBtn.querySelector('.btn-text') : null;

                if(onlineCountEl) onlineCountEl.innerText = result.online;
                
                if(statusTextEl) {
                    statusTextEl.innerText = result.status;
                    if (result.status === 'Offline') {
                        statusTextEl.classList.add('offline');
                    } else {
                        statusTextEl.classList.remove('offline');
                    }
                }

                if(dotEl) {
                    if (result.status === 'Offline') {
                        dotEl.classList.add('offline');
                    } else {
                        dotEl.classList.remove('offline');
                    }
                }

                if(createBtn && btnText) {
                    if (result.status === 'Offline') {
                        createBtn.disabled = true;
                        btnText.innerText = 'INDISPONÍVEL';
                    } else {
                        // Só reabilita se não estiver em processo de criação (sem loader visível)
                        const loader = createBtn.querySelector('.loader');
                        if (loader && loader.style.display === 'none') {
                            createBtn.disabled = false;
                            btnText.innerText = 'CRIAR ACESSO PREMIUM';
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Erro ao atualizar cards:', error);
        }
    };

    updateAllCards();
    setInterval(updateAllCards, 10000); // Atualiza a cada 10 segundos

    // --- Handle Create Button Click (with Ads logic) ---
    const adModal = document.getElementById('ad-modal');
    const adContainer = document.getElementById('reward-ad-container');
    const adTimer = document.getElementById('ad-timer');
    const timerSeconds = document.getElementById('timer-seconds');
    const cancelAdBtn = document.getElementById('cancel-ad-btn');

    let adTimeout = null;
    let adInterval = null;

    window.handleCreateClick = (cardId, hasAds) => {
        const card = document.querySelector(`.server-card[data-card-id="${cardId}"]`);
        const btn = card.querySelector('.create-btn');
        const btnText = btn.querySelector('.btn-text');
        const loader = btn.querySelector('.loader');

        if (hasAds) {
            // Limpa estados anteriores
            if (adTimeout) clearTimeout(adTimeout);
            if (adInterval) clearInterval(adInterval);
            
            // Mostra o modal de anúncio
            adModal.style.display = 'flex';
            adTimer.style.display = 'block';
            
            // Pega o código do anúncio do container oculto no card
            const cardAdSource = document.getElementById(`ads-container-${cardId}`);
            if (cardAdSource && adContainer) {
                adContainer.innerHTML = cardAdSource.innerHTML;
                // Executa scripts dentro do código do anúncio se houver
                const scripts = adContainer.querySelectorAll('script');
                scripts.forEach(oldScript => {
                    const newScript = document.createElement('script');
                    Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                    newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                    oldScript.parentNode.replaceChild(newScript, oldScript);
                });
            }

            // Timer de Recompensa (15 segundos)
            let secondsLeft = 15;
            timerSeconds.innerText = secondsLeft;

            adInterval = setInterval(() => {
                secondsLeft--;
                timerSeconds.innerText = secondsLeft;
                if (secondsLeft <= 0) {
                    clearInterval(adInterval);
                }
            }, 1000);

            adTimeout = setTimeout(() => {
                adModal.style.display = 'none';
                showToast('Recompensa liberada! Criando acesso...', 'success');
                createSSH(cardId, btn, btnText, loader);
            }, 15000); // 15 segundos de anúncio

            // Botão cancelar
            cancelAdBtn.onclick = () => {
                clearTimeout(adTimeout);
                clearInterval(adInterval);
                adModal.style.display = 'none';
                showToast('Anúncio cancelado. Você não recebeu a recompensa.', 'error');
            };

        } else {
            createSSH(cardId, btn, btnText, loader);
        }
    };

    async function createSSH(cardId, btn, btnText, loader) {
        btn.disabled = true;
        btnText.style.display = 'none';
        loader.style.display = 'block';

        try {
            const response = await fetch(`/criar/${cardId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const result = await response.json();

            if (result.success) {
                document.getElementById('res-ip').innerText = result.credentials.ip;
                
                const domainElement = document.getElementById('res-domain');
                const domainContainer = document.getElementById('domain-container');
                if (result.credentials.domain) {
                    domainElement.innerText = result.credentials.domain;
                    domainContainer.style.display = 'block';
                } else {
                    domainContainer.style.display = 'none';
                }

                document.getElementById('res-user').innerText = result.credentials.username;
                document.getElementById('res-pass').innerText = result.credentials.password;
                
                const uuidElement = document.getElementById('res-uuid');
                const uuidContainer = document.getElementById('uuid-container');
                if (result.credentials.uuid) {
                    uuidElement.innerText = result.credentials.uuid;
                    uuidContainer.style.display = 'block';
                } else {
                    uuidContainer.style.display = 'none';
                }

                document.getElementById('res-port').innerText = result.credentials.port;
                document.getElementById('res-expiry').innerText = result.credentials.expiry;

                successModal.style.display = 'flex';
                showToast('Acesso criado com sucesso!', 'success');
            } else {
                showToast(result.message || 'Erro ao criar usuário.', 'error');
            }
        } catch (error) {
            showToast('Erro de conexão.', 'error');
        } finally {
            btn.disabled = false;
            btnText.style.display = 'block';
            loader.style.display = 'none';
        }
    }

    // --- Toast Notification System ---
    window.showToast = (message, type = 'info') => {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };

        toast.innerHTML = `
            <i class="fas ${icons[type] || icons.info}"></i>
            <span class="toast-message">${message}</span>
        `;

        container.appendChild(toast);

        // Auto remove after 5s
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    };
    const copyToClipboardUniversal = (text) => {
        if (navigator.clipboard && window.isSecureContext) {
            // Modern Clipboard API (HTTPS)
            return navigator.clipboard.writeText(text);
        } else {
            // Fallback: execCommand('copy') (HTTP or Older browsers)
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-999999px";
            textArea.style.top = "-999999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            return new Promise((res, rej) => {
                document.execCommand('copy') ? res() : rej();
                textArea.remove();
            });
        }
    };

    // --- Copy All Functionality ---
    copyAllBtn.addEventListener('click', () => {
        const ip = document.getElementById('res-ip').innerText;
        const domain = document.getElementById('res-domain').innerText;
        const user = document.getElementById('res-user').innerText;
        const pass = document.getElementById('res-pass').innerText;
        const uuid = document.getElementById('res-uuid').innerText;
        const port = document.getElementById('res-port').innerText;
        const expiry = document.getElementById('res-expiry').innerText;

        let textToCopy = `🚀 SSH INTEL - ACESSO GERADO\n\n` +
                      `📍 IP: ${ip}\n`;
        
        if (domain && domain !== '---' && domain !== '') {
            textToCopy += `🌐 DOMÍNIO: ${domain}\n`;
        }
        
        textToCopy += `👤 USUÁRIO: ${user}\n` +
                      `🔑 SENHA: ${pass}\n`;
        
        if (uuid && uuid !== '00000000-0000-0000-0000-000000000000') {
            textToCopy += `🆔 UUID XRAY: ${uuid}\n`;
        }

        textToCopy += `🔌 Porta: ${port}\n` +
                      `📅 Expira em: ${expiry}\n\n` +
                      `Obrigado por escolher SSH INTEL!`;

        copyToClipboardUniversal(textToCopy).then(() => {
            showToast('Todas as credenciais copiadas!');
        }).catch(err => {
            showToast('Erro ao copiar!', 'error');
        });
    });

    // --- Clipboard Functionality (Individual) ---
    window.copyToClipboard = (elementId) => {
        const text = document.getElementById(elementId).innerText;
        copyToClipboardUniversal(text).then(() => {
            showToast('Copiado!');
        }).catch(err => {
            console.error('Erro ao copiar:', err);
            showToast('Erro ao copiar!', 'error');
        });
    };

    // --- Toast Notifications ---
    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let icon = '<i class="fas fa-info-circle"></i>';
        if (type === 'success') icon = '<i class="fas fa-check-circle"></i>';
        if (type === 'error') icon = '<i class="fas fa-exclamation-triangle"></i>';

        toast.innerHTML = `${icon} <span>${message}</span>`;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
});
