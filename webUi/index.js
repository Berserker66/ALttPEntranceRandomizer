let monitorFontSize = 16;
let webSocketAddress = 'ws://localhost:5190'; // AOL Instant Messenger port (RIP)
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
    let monitor = document.getElementById('web-input-monitor');
    let newMsg = document.createElement('div');
    newMsg.innerText = event.target.value;
    event.target.value = null;
    monitor.appendChild(newMsg);

    // Scroll to the bottom to keep new messages in view
    monitor.scrollTo(0, monitor.scrollHeight);
}

function appendMonitorCheck(item, location, finder, findee){
    // Identify monitor, create message div
    let monitor = document.getElementById('web-input-monitor');
    let newMsg = document.createElement('div');
    
    // Create item span
    let itemSpan = document.createElement('span');
    itemSpan.innerText = item;
    itemSpan.className = 'item-span';
    
    // Create location span
    let locationSpan = document.createElement('span');
    locationSpan.innerText = location;
    locationSpan.className = 'location-span';
    
    // Create finder span
    let finderSpan = document.createElement('span');
    finderSpan.innerText = finder;
    finderSpan.className = 'finder-span';
    
    // Create findee span
    let findeeSpan = document.createElement('span');
    findeeSpan.innerText = findee + "'s";
    findeeSpan.className = 'findee-span';

    // Build check message and append to monitor
    newMsg.appendChild(finder);
    newMsg.append(' found ');
    newMsg.appendChild(findee);
    newMsg.appendChild(item);
    newMsg.append(' in ');
    newMsg.append(location);
    monitor.appendChild(newMsg);

    // Scroll to the bottom to keep new messages in view
    monitor.scrollTo(0, monitor.scrollHeight);
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

function updateConnectionStatus(snes, server){
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

function handleIncomingMessage(message){
    const data = JSON.parse(message.data);
    switch (data.type){
        case 'connections':
            updateConnectionStatus(parseInt(data.content.snes, 10) === 3, parseInt(data.content.server, 10) === 1);
            break;
        case 'item-check':
            appendMonitorCheck(data.content.item, data.content.location, data.content.finder, data.content.findee);
            break;
        default:
            appendMonitorText(data.content.toString());
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
        webSocket.send(JSON.stringify({
            type: 'webStatus',
            content: 'connections',
        }));

        // Listener for command input
        document.getElementById('web-input').addEventListener('keydown', appendMonitorCommand);
    };

    // Handle incoming messages
    webSocket.onmessage = handleIncomingMessage;
};