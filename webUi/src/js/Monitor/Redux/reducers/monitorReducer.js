import _assign from 'lodash-es/assign';

const initialState = {
  fontSize: 16,
  messageLog: [],
};

const appendToLog = (log, item) => {
  const trimmedLog = log.slice(-499);
  trimmedLog.push(item);
  return trimmedLog;
};

const monitorReducer = (state = initialState, action) => {
  switch (action.type) {
    case 'SET_MONITOR_FONT_SIZE':
      return _assign({}, state, {
        fontSize: action.fontSize,
      });
    case 'APPEND_MESSAGE':
      return _assign({}, state, {
        messageLog: appendToLog(state.messageLog, action.content),
      });
    default:
      return state;
  }
};

export default monitorReducer;
