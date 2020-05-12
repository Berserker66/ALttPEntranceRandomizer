import _assign from 'lodash-es/assign';

const initialState = {
  fontSize: 16,
  showRelevantOnly: false,
  messageLog: [],
};

const appendToLog = (log, item) => {
  const trimmedLog = log.slice(-199);
  trimmedLog.push(item);
  return trimmedLog;
};

const monitorReducer = (state = initialState, action) => {
  switch (action.type) {
    case 'SET_MONITOR_FONT_SIZE':
      return _assign({}, state, {
        fontSize: action.fontSize,
      });

    case 'SET_SHOW_RELEVANT':
      return _assign({}, state, {
        showRelevantOnly: action.showRelevant,
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
