import _assign from 'lodash-es/assign';

const initialState = {
  webSocket: null,
};

const webUIReducer = (state = initialState, action) => {
  switch (action.type) {
    case 'SET_WEBSOCKET':
      return _assign({}, state, {
        webSocket: action.webSocket,
      });
    default:
      return state;
  }
};

export default webUIReducer;
