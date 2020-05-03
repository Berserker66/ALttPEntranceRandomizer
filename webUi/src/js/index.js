import React from 'react';
import ReactDom from 'react-dom';
import { Provider } from 'react-redux';
import { createStore, combineReducers } from 'redux';
import { composeWithDevTools } from 'redux-devtools-extension/developmentOnly';
import WebUI from './WebUI/containers/WebUI';
import '../styles/index.scss';

// Redux reducers
import monitor from './Monitor/Redux/reducers/monitorReducer';
import webUI from './WebUI/Redux/reducers/webUIReducer';

const store = createStore(combineReducers({
  monitor,
  webUI,
}), composeWithDevTools());

const App = () => (
  <Provider store={ store }>
    <WebUI />
  </Provider>
);

window.onload = () => {
  ReactDom.render(<App />, document.getElementById('app'));
};
