# 📢 Guia de Configuração Google AdSense

Este guia detalha como configurar e obter o código de anúncio para o sistema de recompensa do painel **SSH INTEL**.

---

## 🚀 Passo 1: Criar Bloco de Anúncio no Google

Para que o sistema de recompensa funcione, recomendamos o uso de **Anúncios de Display (Banner)** ou **Anúncios In-feed**.

1. Acesse sua conta [Google AdSense](https://www.google.com/adsense).
2. Vá em **Anúncios** > **Por bloco de anúncios**.
3. Selecione **Anúncios de display**.
4. Dê um nome ao bloco (ex: `SSH_Intel_Reward`).
5. No tamanho do anúncio, escolha **Fixo** e defina um tamanho recomendado para modais (ex: **300x250** ou **Responsive**).
6. Clique em **Criar**.

---

## 📋 Passo 2: Copiar o Código

Após criar, o Google fornecerá um código semelhante a este:

```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX"
     crossorigin="anonymous"></script>
<!-- SSH_Intel_Reward -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
     data-ad-slot="XXXXXXXXXX"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({});
</script>
```

---

## ⚙️ Passo 3: Configurar no Painel Admin

Agora que você tem o código, siga estes passos no seu painel SSH INTEL:

1. Acesse o **Painel Administrativo** (`/admin`).
2. Vá na aba **Servidores** (Gerenciar Cards).
3. Escolha o servidor que deseja monetizar e clique no ícone de **Editar** (lápis).
4. No formulário de edição:
   - Ative a opção **Google Ads (Ativar/Desativar)**.
   - No campo **Código do Anúncio**, cole o código completo que você copiou do Google.
5. Clique em **Salvar Alterações**.

---

## 💡 Como funciona para o Usuário?

1. O usuário clica em **"CRIAR ACESSO PREMIUM"**.
2. Uma janela flutuante (modal) se abre exibindo o seu anúncio.
3. Um contador de **15 segundos** inicia automaticamente.
4. Ao final do tempo, o sistema libera o acesso e exibe as credenciais SSH/Xray.

---

## ⚠️ Observações Importantes

* **Ambiente Local**: O Google Ads geralmente não exibe anúncios em `localhost`. Você precisará testar em um domínio real (`http://seu-dominio.com`).
* **Políticas do Google**: Certifique-se de que o posicionamento do anúncio não viola as políticas do Google AdSense para evitar banimentos.
* **Tamanho do Bloco**: Use tamanhos que caibam bem em dispositivos móveis, pois a maioria dos usuários de SSH utiliza celulares.
