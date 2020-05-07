import _assign from 'lodash-es/assign';

const initialState = {
  connections: {
    snesConnected: false,
    serverConnected: false,
  },
  hints: {
    hintCost: null,
    checkPoints: null,
    playerPoints: 0,
  },
};

const gameStateReducer = (state = initialState, action) => {
  switch (action.type) {
    case 'UPDATE_GAME_STATE':
      return _assign({}, state, action.gameState);

    default:
      return state;
  }
};

export default gameStateReducer;
