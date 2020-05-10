import React, { Component } from 'react';
import { connect } from 'react-redux';
import '../../../styles/WidgetArea/containers/WidgetArea.scss';

class WidgetArea extends Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  saveNotes = (event) => {
    sessionStorage.setItem('notes', event.target.value);
  };

  render() {
    return (
      <div id="widget-area">
        <div id="notes">
          Notes:<br />
          <textarea defaultValue={ sessionStorage.getItem('notes') } onKeyUp={ this.saveNotes } />
        </div>
        More tools Coming Soon™
      </div>
    );
  }
}

export default connect()(WidgetArea);
