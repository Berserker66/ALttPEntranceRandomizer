import React, { Component } from 'react';
import { connect } from 'react-redux';
import WebSocketUtils from '../../global/WebSocketUtils';
import '../../../styles/Monitor/containers/MonitorControls.scss';

// Redux actions
import setMonitorFontSize from '../Redux/actions/setMonitorFontSize';

const mapReduxStateToProps = (reduxState) => ({
  fontSize: reduxState.monitor.fontSize,
});

const mapDispatchToProps = (dispatch) => ({
  updateFontSize: (fontSize) => {
    dispatch(setMonitorFontSize(fontSize));
  },
});

class MonitorControls extends Component {
  constructor(props) {
    super(props);
    this.localRef = React.createRef();
    this.state = {
      snesConnected: false,
      serverConnected: false,
    };
  }

  componentDidMount() {
    WebSocketUtils.attachSocketListener(this.localRef.current, this.handleSocketMessage);
  }

  handleSocketMessage = (event) => {
    console.log(event);
  };

  increaseTextSize = () => {
    if (this.props.fontSize >= 25) return;
    this.props.updateFontSize(this.props.fontSize + 1);
  };

  decreaseTextSize = () => {
    if (this.props.fontSize <= 10) return;
    this.props.updateFontSize(this.props.fontSize - 1);
  };

  render() {
    return (
      <div id="monitor-controls" ref={ this.localRef }>
        <div id="connection-status">
          <table id="connection-status-table">
            <tbody>
              <tr>
                <td>SNES Status:</td>
                <td>
                  <span className={ this.state.snesConnected ? 'connected' : 'not-connected' }>
                    { this.state.snesConnected ? 'Connected' : 'Not Connected' }
                  </span>
                </td>
              </tr>
              <tr>
                <td>Server Status:</td>
                <td>
                  <span className={ this.state.serverConnected ? 'connected' : 'not-connected' }>
                    { this.state.serverConnected ? 'Connected' : 'Not Connected' }
                  </span>
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
