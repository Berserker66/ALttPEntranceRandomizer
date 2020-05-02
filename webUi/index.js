let monitorFontSize = 16;
let webSocketAddress = 'ws://localhost:5190'; // AOL Instant Messenger port (RIP)
let webServerAddress = null;
let webSocket = null;

function appendMonitorText(str){
    let monitor = document.getElementById('web-input-monitor');
    let newMsg = document.createElement('div');
    newMsg.innerText = str;
    monitor.appendChild(newMsg);

    // Scroll to the bottom to keep new messages in view
    monitor.scrollTo(0, monitor.scrollHeight);
}

function appendMonitorCommand(event){
    // Only append a monitor message if the user pressed enter and the command is not empty
    if(event.key !== 'Enter' || !event.target.value) return;

    // Send the command to the client
    webSocket.send(JSON.stringify({ type: 'webCommand', content: event.target.value }));

    // Append command to monitor
    const monitor = document.getElementById('web-input-monitor');
    const newMsg = document.createElement('div');
    newMsg.className = 'user-command';
    newMsg.innerText = event.target.value;
    event.target.value = null;
    monitor.appendChild(newMsg);

    // Scroll to the bottom to keep new messages in view
    monitor.scrollTo(0, monitor.scrollHeight);
}

function appendItemCheck(item, location, finder, recipient=null){
    // Identify monitor, create message div
    let monitor = document.getElementById('web-input-monitor');
    let newMsg = document.createElement('div');

    // Build spans
    const finderSpan = buildFinderSpan(finder);
    const itemSpan = buildItemSpan(item);
    const locationSpan = buildLocationSpan(location);

    // Found someone else's item
    if (recipient !== null) {
        const recipientSpan = buildRecipientSpan(recipient, true);

        // Build check message and append to monitor
        newMsg.appendChild(finderSpan);
        newMsg.append(' found ');
        newMsg.appendChild(recipientSpan);
        newMsg.appendChild(itemSpan);
        newMsg.append(' at ');
        newMsg.append(locationSpan);
        monitor.appendChild(newMsg);
    }else{
        // Found your own item
        newMsg.appendChild(finderSpan);
        newMsg.append(' found their own ');
        newMsg.appendChild(itemSpan);
        newMsg.append(' at ');
        newMsg.appendChild(locationSpan);
        monitor.appendChild(newMsg);
    }

    // Scroll to the bottom to keep new messages in view
    monitor.scrollTo(0, monitor.scrollHeight);
}

function appendHint(finder, recipient, item, location){
    console.log(`${finder} ${recipient} ${item} ${location}`);

    // Identify monitor, create message div
    let monitor = document.getElementById('web-input-monitor');
    let newMsg = document.createElement('div');

    const finderSpan = buildFinderSpan(finder, true);
    const recipientSpan = buildRecipientSpan(recipient, true);
    const itemSpan = buildItemSpan(item);
    const locationSpan = buildLocationSpan(location);

    newMsg.appendChild(recipientSpan);
    newMsg.appendChild(itemSpan);
    newMsg.append(' can be found in ');
    newMsg.appendChild(finderSpan);
    newMsg.append(' world at ');
    newMsg.appendChild(locationSpan);
    monitor.appendChild(newMsg);

    // Scroll to the bottom to keep new messages in view
    monitor.scrollTo(0, monitor.scrollHeight);
}

function buildItemSpan(item) {
    const itemSpan = document.createElement('span');
    itemSpan.innerText = item;
    itemSpan.className = 'item-span';
    return itemSpan;
}

function buildLocationSpan(location) {
    const locationSpan = document.createElement('span');
    locationSpan.innerText = location;
    locationSpan.className = 'location-span';
    return locationSpan;
}

function buildFinderSpan(finder, possessive=false) {
    const finderSpan = document.createElement('span');
    finderSpan.innerText = finder + `${possessive ? "'s" : ''} `;
    finderSpan.className = 'finder-span';
    return finderSpan;
}

function buildRecipientSpan(recipient, possessive=false) {
    const recipientSpan = document.createElement('span');
    recipientSpan.innerText = recipient + `${possessive ? "'s" : ''} `;
    recipientSpan.className = 'recipient-span';
    return recipientSpan;
}

function increaseText(){
    if (monitorFontSize === 100) return;
    monitorFontSize++;
    let monitor = document.getElementById('web-input-monitor');
    monitor.style.fontSize = monitorFontSize+'px';
    document.getElementById('text-size').innerText = monitorFontSize + '';
}

function decreaseText(){
    if (monitorFontSize === 1) return;
    monitorFontSize--;
    let monitor = document.getElementById('web-input-monitor');
    monitor.style.fontSize = monitorFontSize+'px';
    document.getElementById('text-size').innerText = monitorFontSize + '';
}

function setMonitorHeight(){
    // Window height - header height - command interface height - margin adjustments
        document.getElementById('web-input-monitor').style.height = (window.innerHeight - 119 - 23 - 20) + 'px';
}

function updateConnectionStatusUi(snes, server){
    let snesStatus = document.getElementById('qusb2snes');
    let multiServer = document.getElementById('multi-server');

    // SNES Status
    if (snes){
        snesStatus.innerText = 'Connected';
        snesStatus.style.color = 'forestgreen';
    }else{
        snesStatus.innerText = 'Not Connected';
        snesStatus.style.color = 'red';
    }

    // MultiServer Status
    if(server){
        multiServer.innerText = 'Connected';
        multiServer.style.color = 'forestgreen';
    }else{
        multiServer.innerText = 'Not Connected';
        multiServer.style.color = 'red';
    }
}

function serverConnect(event=null){
    if (event) { event.preventDefault(); }
    if (!webServerAddress || !!event) {
        webServerAddress = prompt("Please enter multiworld server address:");
    }
    sendSocketData('webConfig', { serverAddress: webServerAddress });
}

function handleIncomingMessage(message){
    const data = JSON.parse(message.data);
    switch (data.type){
        case 'connections':
            updateConnectionStatusUi(parseInt(data.content.snes, 10) === 3, parseInt(data.content.server, 10) === 1);
            break;
        case 'serverAddress':
            serverConnect();
            break;
        case 'itemSent':
            appendItemCheck(data.content.item, data.content.location, data.content.finder, data.content.recipient);
            break;
        case 'itemFound':
            appendItemCheck(data.content.item, data.content.location, data.content.finder);
            break;
        case 'hint':
            appendHint(data.content.finder, data.content.recipient, data.content.item, data.content.location);
            break;
        default:
            appendMonitorText(data.content.toString());
    }
}

function sendSocketData(type, data) {
    if (webSocket) {
        webSocket.send(JSON.stringify({
            type: type,
            content: data,
        }));
    }
}

window.onload = () => {
    // Listeners for accessibility options
    document.getElementById('text-size').innerText = monitorFontSize + '';
    document.getElementById('increase-text-size').addEventListener('click', increaseText);
    document.getElementById('decrease-text-size').addEventListener('click', decreaseText);

    // Listeners for monitor adjustments
    window.onresize = () => { setMonitorHeight() };
    setMonitorHeight();

    // Establish connection to MultiClient
    webSocket = new WebSocket(webSocketAddress);
    webSocket.onerror = (event) => {
        appendMonitorText(`Unable to connect to websocket server at ${webSocketAddress}`);
        setTimeout(() => { webSocket = new WebSocket(webSocketAddress); }, 5000)
    };
    webSocket.onclose = (event) => { console.log(event); };
    webSocket.onopen = () => {
        appendMonitorText("Websocket connected");
        sendSocketData('webStatus', 'connections');

        // Listener for command input
        document.getElementById('web-input').addEventListener('keydown', appendMonitorCommand);

        // Listener for connect button
        document.getElementById('server-connect').addEventListener('click', serverConnect);
    };

    // Handle incoming messages
    webSocket.onmessage = handleIncomingMessage;
};