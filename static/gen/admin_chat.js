class AdminChatDashboard{constructor(){this.socket=null;this.activeSessionId=null;this.activeCustomerId=null;this.isConnected=false;this.isMobile=window.innerWidth<=992;this.initializeElements();this.init();}
initializeElements(){this.sessionList=document.getElementById('sessionList');this.chatSidebar=document.getElementById('chatSidebar');this.welcomeScreen=document.getElementById('chatWelcomeScreen');this.activeScreen=document.getElementById('chatActiveScreen');this.messagesContainer=document.querySelector('.messages-scroll-area');this.customerNameEl=document.getElementById('activeCustomerName');this.chatInput=document.getElementById('chatInput');this.chatForm=document.getElementById('chatInputForm');this.sendBtn=document.getElementById('chatSendBtn');this.charCounter=document.querySelector('.char-counter');this.sidebarToggle=document.getElementById('sidebar-toggle');this.sidebarClose=document.getElementById('sidebarClose');this.sidebarOverlay=document.getElementById('sidebarOverlay');this.userDetailsToggle=document.getElementById('userDetailsToggle');this.userDetailsPanel=document.getElementById('userDetailsPanel');this.userDetailsPanelClose=document.getElementById('userDetailsPanelClose');this.userDetailsContent=document.getElementById('userDetailsContent');this.userDetailsModal=document.getElementById('userDetailsModal');this.userDetailsModalClose=document.getElementById('userDetailsModalClose');this.userDetailsModalContent=document.getElementById('userDetailsModalContent');}
init(){console.log('🔧 Initializing Admin Chat Dashboard');this.bindEvents();this.connectSocket();this.setupResponsiveHandling();this.checkPreselectedSession();this.updateCharCounter();}
bindEvents(){if(this.sessionList){this.sessionList.addEventListener('click',(e)=>{const conversationItem=e.target.closest('.conversation-item');if(conversationItem){this.selectConversation(conversationItem);}});}
if(this.chatForm){this.chatForm.addEventListener('submit',(e)=>{e.preventDefault();this.sendMessage();});}
if(this.chatInput){this.chatInput.addEventListener('input',()=>{this.autoResizeTextarea();this.updateCharCounter();});this.chatInput.addEventListener('keydown',(e)=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();this.sendMessage();}});}
if(this.sidebarToggle){this.sidebarToggle.addEventListener('click',()=>{this.showSidebar();});}
if(this.sidebarClose){this.sidebarClose.addEventListener('click',()=>{this.hideSidebar();});}
if(this.sidebarOverlay){this.sidebarOverlay.addEventListener('click',()=>{this.hideSidebar();});}
if(this.userDetailsToggle){this.userDetailsToggle.addEventListener('click',()=>{this.showUserDetails();});}
if(this.userDetailsPanelClose){this.userDetailsPanelClose.addEventListener('click',()=>{this.hideUserDetails();});}
if(this.userDetailsModalClose){this.userDetailsModalClose.addEventListener('click',()=>{this.hideUserDetailsModal();});}
if(this.userDetailsModal){this.userDetailsModal.addEventListener('click',(e)=>{if(e.target===this.userDetailsModal){this.hideUserDetailsModal();}});}
document.addEventListener('keydown',(e)=>{if(e.key==='Escape'){this.hideSidebar();this.hideUserDetailsModal();}});window.addEventListener('resize',()=>{this.handleResize();});}
createNewConversationElement(data){const conversationItem=document.createElement('div');conversationItem.className='conversation-item';conversationItem.dataset.sessionId=data.session_id;conversationItem.dataset.customerId=data.customer_id;conversationItem.innerHTML=`<div class="conversation-avatar"><i class="fas fa-user"></i></div><div class="conversation-details"><div class="conversation-name">${data.customer_name}</div><div class="conversation-status">New</div><div class="conversation-preview">${data.message}</div></div><div class="conversation-meta"><div class="conversation-time">${data.timestamp}</div><div class="notification-dot"></div></div>`;return conversationItem;}
connectSocket(){try{this.socket=io();this.socket.on('connect',()=>{console.log('💬 Admin connected to chat server');this.isConnected=true;this.updateConnectionState();});this.socket.on('disconnect',()=>{console.log('💬 Admin disconnected from chat server');this.isConnected=false;this.updateConnectionState();});this.socket.on('chat_history',(data)=>{this.renderChatHistory(data.history);});this.socket.on('receive_message',(data)=>{if(data.sender_type==='agent')return;const sessionElement=this.sessionList.querySelector(`[data-session-id="${data.session_id}"]`);if(sessionElement){if(this.activeSessionId==data.session_id){this.addMessage(data.message,'user',data.timestamp);}else{this.showNotificationDot(data.session_id);}
const preview=sessionElement.querySelector('.conversation-preview');if(preview)preview.textContent=data.message;}else{const newConversation=this.createNewConversationElement(data);const emptyState=this.sessionList.querySelector('.empty-conversations');if(emptyState){emptyState.remove();}
this.sessionList.prepend(newConversation);}});}catch(error){console.error('Failed to connect to chat server:',error);this.isConnected=false;this.updateConnectionState();}}
setupResponsiveHandling(){this.handleResize();}
handleResize(){const wasMobile=this.isMobile;this.isMobile=window.innerWidth<=992;if(wasMobile!==this.isMobile){this.hideSidebar();this.hideUserDetails();this.hideUserDetailsModal();}}
checkPreselectedSession(){const preselectedSessionId=document.body.dataset.preselectedSessionId;if(preselectedSessionId&&this.sessionList){const targetSession=this.sessionList.querySelector(`[data-session-id="${preselectedSessionId}"]`);if(targetSession){setTimeout(()=>{this.selectConversation(targetSession);},100);}}}
selectConversation(conversationElement){this.sessionList.querySelectorAll('.conversation-item.active').forEach(item=>item.classList.remove('active'));conversationElement.classList.add('active');this.activeSessionId=conversationElement.dataset.sessionId;this.activeCustomerId=conversationElement.dataset.customerId;const notificationDot=conversationElement.querySelector('.notification-dot');if(notificationDot){notificationDot.classList.add('hidden');}
this.showActiveScreen();this.updateCustomerName(conversationElement.querySelector('.conversation-name').textContent);if(this.socket&&this.isConnected){this.socket.emit('request_history',{session_id:this.activeSessionId});}
this.loadUserDetails();if(this.isMobile){this.hideSidebar();}
if(this.chatInput){setTimeout(()=>this.chatInput.focus(),100);}}
showActiveScreen(){if(this.welcomeScreen){this.welcomeScreen.style.display='none';}
if(this.activeScreen){this.activeScreen.classList.remove('hidden');}}
hideActiveScreen(){if(this.welcomeScreen){this.welcomeScreen.style.display='flex';}
if(this.activeScreen){this.activeScreen.classList.add('hidden');}}
updateCustomerName(name){if(this.customerNameEl){this.customerNameEl.textContent=name;}}
renderChatHistory(history){if(!this.messagesContainer)return;this.messagesContainer.innerHTML='';if(history.length===0){this.addSystemMessage('No messages in this conversation yet.');return;}
history.forEach(msg=>{this.addMessage(msg.message_text,msg.sender_type,msg.timestamp);});}
addMessage(content,senderType,timestamp=null){if(!this.messagesContainer)return;const messageEl=document.createElement('div');messageEl.className=`chat-message ${senderType}`;const bubbleEl=document.createElement('div');bubbleEl.className='message-bubble';bubbleEl.textContent=content;const timestampEl=document.createElement('div');timestampEl.className='message-timestamp';timestampEl.textContent=timestamp||this.formatTimestamp(new Date());messageEl.appendChild(bubbleEl);messageEl.appendChild(timestampEl);this.messagesContainer.appendChild(messageEl);this.scrollToBottom();}
addSystemMessage(content){this.addMessage(content,'system');}
sendMessage(){if(!this.chatInput||!this.activeCustomerId||!this.isConnected)return;const message=this.chatInput.value.trim();if(!message)return;if(message.length>500){this.showError('Message too long. Please keep it under 500 characters.');return;}
this.socket.emit('agent_send_message',{message:message,customer_id:this.activeCustomerId});this.addMessage(message,'agent');this.chatInput.value='';this.autoResizeTextarea();this.updateCharCounter();this.chatInput.focus();}
autoResizeTextarea(){if(!this.chatInput)return;this.chatInput.style.height='auto';const newHeight=Math.min(this.chatInput.scrollHeight,100);this.chatInput.style.height=newHeight+'px';}
updateCharCounter(){if(!this.charCounter||!this.chatInput)return;const current=this.chatInput.value.length;const max=500;this.charCounter.textContent=`${current}/${max}`;if(current>max){this.charCounter.classList.add('over-limit');this.sendBtn.disabled=true;}else{this.charCounter.classList.remove('over-limit');this.sendBtn.disabled=!this.isConnected;}}
updateConnectionState(){if(this.sendBtn){this.sendBtn.disabled=!this.isConnected;}
if(!this.isConnected){this.addSystemMessage('Connection lost. Trying to reconnect...');}}
loadUserDetails(){if(!this.activeCustomerId)return;this.showUserDetailsLoading();fetch(`/api/user_details/${this.activeCustomerId}`).then(response=>{if(!response.ok){throw new Error('Failed to load user details');}
return response.json();}).then(data=>{this.renderUserDetails(data);}).catch(error=>{console.error('Error loading user details:',error);this.showUserDetailsError();});}
showUserDetailsLoading(){const content=`<div class="loading-state"><i class="fas fa-spinner fa-spin"></i><p>Loading customer details...</p></div>`;if(this.userDetailsContent){this.userDetailsContent.innerHTML=content;}
if(this.userDetailsModalContent){this.userDetailsModalContent.innerHTML=content;}}
renderUserDetails(data){const content=`<div class="user-detail-item"><span class="detail-label">Username</span><span class="detail-value">${data.username||'N/A'}</span></div><div class="user-detail-item"><span class="detail-label">Full Name</span><span class="detail-value">${data.full_name||'N/A'}</span></div><div class="user-detail-item"><span class="detail-label">Email</span><span class="detail-value">${data.email||'N/A'}</span></div><div class="user-detail-item"><span class="detail-label">Phone</span><span class="detail-value">${data.phone_number||'N/A'}</span></div><div class="user-detail-item"><span class="detail-label">Account Tier</span><span class="detail-value">${data.account_tier||'Standard'}</span></div><div class="user-detail-item"><span class="detail-label">Member Since</span><span class="detail-value">${data.date_joined||'N/A'}</span></div>`;if(this.userDetailsContent){this.userDetailsContent.innerHTML=content;}
if(this.userDetailsModalContent){this.userDetailsModalContent.innerHTML=content;}}
showUserDetailsError(){const content=`<div class="loading-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load customer details</p></div>`;if(this.userDetailsContent){this.userDetailsContent.innerHTML=content;}
if(this.userDetailsModalContent){this.userDetailsModalContent.innerHTML=content;}}
showSidebar(){if(this.chatSidebar){this.chatSidebar.classList.add('active');}
if(this.sidebarOverlay){this.sidebarOverlay.classList.add('active');}
document.body.style.overflow='hidden';}
hideSidebar(){if(this.chatSidebar){this.chatSidebar.classList.remove('active');}
if(this.sidebarOverlay){this.sidebarOverlay.classList.remove('active');}
document.body.style.overflow='';}
showUserDetails(){if(this.isMobile){this.showUserDetailsModal();}else{if(this.userDetailsPanel){this.userDetailsPanel.classList.remove('hidden');}}}
hideUserDetails(){if(this.userDetailsPanel){this.userDetailsPanel.classList.add('hidden');}}
showUserDetailsModal(){if(this.userDetailsModal){this.userDetailsModal.classList.remove('hidden');}
document.body.style.overflow='hidden';}
hideUserDetailsModal(){if(this.userDetailsModal){this.userDetailsModal.classList.add('hidden');}
document.body.style.overflow='';}
showNotificationDot(sessionId){const sessionElement=this.sessionList.querySelector(`[data-session-id="${sessionId}"]`);if(sessionElement){const dot=sessionElement.querySelector('.notification-dot');if(dot){dot.classList.remove('hidden');}}}
scrollToBottom(){if(this.messagesContainer){requestAnimationFrame(()=>{this.messagesContainer.scrollTop=this.messagesContainer.scrollHeight;});}}
formatTimestamp(date){return date.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});}
showError(message){console.error(message);alert(message);}}
document.addEventListener('DOMContentLoaded',()=>{new AdminChatDashboard();});