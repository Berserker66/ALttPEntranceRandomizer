class WebSocketUtils {
  static formatSocketData = (eventType, content) => JSON.stringify({
    type: eventType,
    content,
  });

  static attachSocketListener = (object, callback) => {
    object.addEventListener('webSocketMessage', callback);
  };
}

export default WebSocketUtils;
