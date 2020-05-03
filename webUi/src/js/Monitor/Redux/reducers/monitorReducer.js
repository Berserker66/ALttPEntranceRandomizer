import _assign from 'lodash-es/assign';

const initialState = {
  fontSize: 16,
};

const monitorReducer = (state = initialState, action) => {
  switch (action.type) {
    case 'SET_MONITOR_FONT_SIZE':
      return _assign({}, state, {
        fontSize: action.fontSize,
      });
    default:
      return state;
  }
};

export default monitorReducer;
