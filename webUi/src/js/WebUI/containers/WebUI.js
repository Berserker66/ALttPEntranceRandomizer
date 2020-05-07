import React, { Component } from 'react';
import { connect } from 'react-redux';
import HeaderBar from '../../HeaderBar/components/HeaderBar';
import Monitor from '../../Monitor/components/Monitor';
import '../../../styles/WebUI/containers/WebUI.scss';

// Redux actions
import setWebSocket from '../Redux/actions/setWebSocket';
import WebSocketUtils from '../../global/WebSocketUtils';

const mapDispatchToProps = (dispatch) => ({
  doSetWebSocket: (webSocket) => dispatch(setWebSocket(webSocket)),
  handleIncomingMessage: (message) => dispatch(WebSocketUtils.handleIncomingMessage(message)),
});

class WebUI extends Component {
  constructor(props) {
    super(props);
    this.webSocket = null;
    this.webUiRef = React.createRef();
  }

  componentDidMount() {
    this.webSocketConnect();
  }

  webSocketConnect = () => {
    const webSocketAddress = 'ws://localhost:5190'; // AOL Instant Messenger port (RIP)
    try {
      this.props.webSocket.close();
      this.props.doSetWebSocket(null);
    } catch (error) {
      // Ignore errors caused by attempting to close an invalid WebSocket object
    }

    const webSocket = new WebSocket(webSocketAddress);
    webSocket.onerror = () => {
      setTimeout(this.webSocketConnect, 5000);
    };
    webSocket.onclose = () => {
      // If the WebSocket connection is closed for some reason, attempt to reconnect
      setTimeout(this.webSocketConnect, 5000);
    };

    // Dispatch a custom event when websocket messages are received
    webSocket.onmessage = (message) => {
      this.props.handleIncomingMessage(message);
    };

    // Store the webSocket object in the Redux store so other components can access it
    webSocket.onopen = () => {
      this.props.doSetWebSocket(webSocket);
      webSocket.send(WebSocketUtils.formatSocketData('webStatus', 'connections'));
    };
  };

  render() {
    return (
      <div id="web-ui" ref={ this.webUiRef }>
        <HeaderBar />
        <Monitor />
      </div>
    );
  }
}

export default connect(null, mapDispatchToProps)(WebUI);
