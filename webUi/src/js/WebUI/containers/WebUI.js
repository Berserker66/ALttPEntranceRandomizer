import React, { Component } from 'react';
import { connect } from 'react-redux';
import HeaderBar from '../../HeaderBar/components/HeaderBar';
import Monitor from '../../Monitor/components/Monitor';
import WebSocketUtils from '../../global/WebSocketUtils';
import '../../../styles/WebUI/containers/WebUI.scss';

// Redux actions
import setWebSocket from '../Redux/actions/setWebSocket';

const mapDispatchToProps = (dispatch) => ({
  doSetWebSocket: (webSocket) => dispatch(setWebSocket(webSocket)),
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
      this.dispatchSocketEvent('socketError', `Unable to connect to websocket server at ${webSocketAddress}`);
      setTimeout(this.webSocketConnect, 5000);
    };
    webSocket.onclose = () => {
      // If the WebSocket connection is closed for some reason, attempt to reconnect
      setTimeout(this.webSocketConnect, 5000);
    };
    webSocket.onopen = () => {
      webSocket.send(WebSocketUtils.formatSocketData('webStatus', 'connections'));
    };

    // Dispatch a custom event when websocket messages are received
    webSocket.onmessage = (message) => {
      const data = JSON.parse(message.data);
      this.dispatchSocketEvent(data.type, data.content);
    };

    // Store the webSocket object in the Redux store so other components can access it
    this.props.doSetWebSocket(webSocket);
  };

  /**
   * Dispatch a custom DOM event containing the message received by the websocket
   * @param eventType
   * @param content
   */
  dispatchSocketEvent = (eventType, content) => {
    const webSocketEvent = new CustomEvent('webSocketMessage', {
      detail: { type: eventType, content },
    });
    this.webUiRef.current.dispatchEvent(webSocketEvent);
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
