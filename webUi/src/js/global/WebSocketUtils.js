import MonitorTools from './MonitorTools';

// Redux actions
import appendMessage from '../Monitor/Redux/actions/appendMessage';
import updateGameState from './Redux/actions/updateGameState';

class WebSocketUtils {
  static formatSocketData = (eventType, content) => JSON.stringify({
    type: eventType,
    content,
  });

  /**
   * Handle incoming websocket data and return appropriate data for dispatch
   * @param message
   * @returns Object
   */
  static handleIncomingMessage = (message) => {
    try {
      const data = JSON.parse(message.data);

      switch (data.type) {
        // Client sent snes and server connection statuses
        case 'connections':
          return updateGameState({
            connections: {
              snesConnected: parseInt(data.content.snes, 10) === 3,
              serverConnected: parseInt(data.content.server, 10) === 1,
            },
          });

        // Client unable to automatically connect to multiworld server
        case 'serverAddress':
          return appendMessage(MonitorTools.createTextDiv(
            'Unable to automatically connect to multiworld server. Please enter an address manually.',
          ));

        case 'itemSent':
          return appendMessage(MonitorTools.sentItem(data.content.finder, data.content.recipient,
            data.content.item, data.content.location));

        case 'itemReceived':
          return appendMessage(MonitorTools.receivedItem(data.content.finder, data.content.item,
            data.content.location, data.content.itemIndex, data.content.queueLength));

        case 'itemFound':
          return appendMessage(MonitorTools.foundItem(data.content.finder, data.content.item, data.content.location));

        case 'hint':
          return appendMessage(MonitorTools.hintMessage(data.content.finder, data.content.recipient,
            data.content.item, data.content.location), parseInt(data.content.found, 10) === 1);

        // The client prints several types of messages to the console
        case 'critical':
        case 'error':
        case 'warning':
        case 'info':
        case 'chat':
          return appendMessage(MonitorTools.createTextDiv(
            (typeof (data.content) === 'string') ? data.content : JSON.stringify(data.content),
          ));
        default:
          console.warn(`Unknown message type received: ${data.type}`);
          console.warn(data.content);
          return { type: 'NO_OP' };
      }
    } catch (error) {
      console.error(message);
      console.error(error);
      // The returned value from this function will be dispatched to Redux. If an error occurs,
      // Redux and the SPA in general should live on. Dispatching something with the correct format
      // but that matches no known Redux action will cause the state to update to itself, which is
      // treated as a no-op.
      return { type: 'NO_OP' };
    }
  };
}

export default WebSocketUtils;
