import React, { Component } from 'react';
import { connect } from 'react-redux';
import WebSocketUtils from '../../global/WebSocketUtils';
import '../../../styles/Monitor/containers/MonitorWindow.scss';

const mapReduxStateToProps = (reduxState) => ({
  fontSize: reduxState.monitor.fontSize,
  webSocket: reduxState.webUI.webSocket,
  messageLog: reduxState.monitor.messageLog,
  showRelevantOnly: reduxState.monitor.showRelevantOnly,
});

class MonitorWindow extends Component {
  constructor(props) {
    super(props);
    this.monitorRef = React.createRef();
    this.commandRef = React.createRef();
    this.commandInputRef = React.createRef();
  }

  componentDidMount() {
    // Adjust the monitor height to match user's viewport
    this.adjustMonitorHeight();

    // Resize the monitor as the user adjusts the window size
    window.addEventListener('resize', this.adjustMonitorHeight);
  }

  componentDidUpdate() {
    this.monitorRef.current.style.fontSize = `${this.props.fontSize}px`;
    this.adjustMonitorHeight();
  }

  componentWillUnmount() {
    // If one day we have different components occupying the main viewport, let us not attempt to
    // perform actions on an unmounted component
    window.removeEventListener('resize', this.adjustMonitorHeight);
  }

  adjustMonitorHeight = () => {
    const monitorDimensions = this.monitorRef.current.getBoundingClientRect();
    const commandDimensions = this.commandRef.current.getBoundingClientRect();

    // Set monitor height
    const newMonitorHeight = window.innerHeight - monitorDimensions.top - commandDimensions.height - 30;
    this.monitorRef.current.style.height = `${newMonitorHeight}px`;
    this.scrollToBottom();
  };

  scrollToBottom = () => {
    this.monitorRef.current.scrollTo(0, this.monitorRef.current.scrollHeight);
  };

  sendCommand = (event) => {
    // If the user didn't press enter, or the command is empty, do nothing
    if (event.key !== 'Enter' || !event.target.value) return;

    const newMsg = document.createElement('div');
    newMsg.innerText = event.target.value;
    newMsg.className = 'user-command';
    this.monitorRef.current.appendChild(newMsg);
    this.scrollToBottom();
    this.props.webSocket.send(WebSocketUtils.formatSocketData('webCommand', event.target.value));
    this.commandInputRef.current.value = '';
  };

  render() {
    return (
      <div id="monitor-window-wrapper">
        <div
          id="monitor-window"
          ref={ this.monitorRef }
          className={ `${this.props.showRelevantOnly ? 'relevant-only' : null}` }
        >
          { this.props.messageLog }
        </div>
        <div id="command-wrapper" ref={ this.commandRef }>
          Command: <input onKeyDown={ this.sendCommand } ref={ this.commandInputRef } />
        </div>
      </div>
    );
  }
}

export default connect(mapReduxStateToProps)(MonitorWindow);
