import React, { Component } from 'react';
import { connect } from 'react-redux';
import '../../../styles/Monitor/containers/MonitorControls.scss';

// Redux actions
import setMonitorFontSize from '../Redux/actions/setMonitorFontSize';
import WebSocketUtils from "../../global/WebSocketUtils";

const mapReduxStateToProps = (reduxState) => ({
  fontSize: reduxState.monitor.fontSize,
  webSocket: reduxState.webUI.webSocket,
  snesConnected: reduxState.gameState.connections.snesConnected,
  serverConnected: reduxState.gameState.connections.serverConnected,
});

const mapDispatchToProps = (dispatch) => ({
  updateFontSize: (fontSize) => {
    dispatch(setMonitorFontSize(fontSize));
  },
});

class MonitorControls extends Component {
  increaseTextSize = () => {
    if (this.props.fontSize >= 25) return;
    this.props.updateFontSize(this.props.fontSize + 1);
  };

  decreaseTextSize = () => {
    if (this.props.fontSize <= 10) return;
    this.props.updateFontSize(this.props.fontSize - 1);
  };

  jankServerPrompt = () => {
    const serverAddress = prompt('Enter multiworld server address:');
    if (!serverAddress) return;
    this.props.webSocket.send(WebSocketUtils.formatSocketData('webConfig', { serverAddress }));
  };

  render() {
    return (
      <div id="monitor-controls">
        <div id="connection-status">
          <table id="connection-status-table">
            <tbody>
              <tr>
                <td>SNES Status:</td>
                <td>
                  <span className={ this.props.snesConnected ? 'connected' : 'not-connected' }>
                    { this.props.snesConnected ? 'Connected' : 'Not Connected' }
                  </span>
                </td>
              </tr>
              <tr>
                <td>Server Status:</td>
                <td>
                  {
                    this.props.snesConnected && !this.props.serverConnected ?
                      (
                        <button onClick={ this.jankServerPrompt }>Enter Address</button>
                      ) : (
                        <span className={ this.props.serverConnected ? 'connected' : 'not-connected' }>
                          { this.props.serverConnected ? 'Connected' : 'Not Connected' }
                        </span>
                      )
                  }
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div id="accessibility">
          Text Size:
          <button disabled={ this.props.fontSize <= 10 } onClick={ this.decreaseTextSize }>-</button>
          { this.props.fontSize }
          <button disabled={ this.props.fontSize >= 25 } onClick={ this.increaseTextSize }>+</button>
        </div>
      </div>
    );
  }
}

export default connect(mapReduxStateToProps, mapDispatchToProps)(MonitorControls);
