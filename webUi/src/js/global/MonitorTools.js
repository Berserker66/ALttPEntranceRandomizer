import React from 'react';
import md5 from 'crypto-js/md5';

const finderSpan = (finder, possessive = false) => (
  <span className="finder-span">{finder}{possessive ? "'s" : null}</span>
);
const recipientSpan = (recipient, possessive = false) => (
  <span className="recipient-span">{recipient}{possessive ? "'s" : null}</span>
);
const itemSpan = (item) => <span className="item-span">{item}</span>;
const locationSpan = (location) => <span className="location-span">{location}</span>;

class MonitorTools {
  /** Convert plaintext into a React-friendly div */
  static createTextDiv = (text) => <div key={ md5(text) }>{text}</div>;

  /** Sent an item to another player */
  static sentItem = (finder, recipient, item, location) => (
    <div key={ md5(`${finder}${recipient}${item}${location}`) }>
      {finderSpan(finder)} found {recipientSpan(recipient, true)} {itemSpan(item)} at {locationSpan(location)}
    </div>
  )

  /** Received item from another player */
  static receivedItem = (finder, item, location, itemIndex, queueLength) => (
    <div key={ md5(`${finder}${item}${location}`) }>
      {finderSpan(finder)} found your {itemSpan(item)} at {locationSpan(location)} ({itemIndex}/{queueLength} in queue)
    </div>
  )

  /** Player found their own item (local or remote player) */
  static foundItem = (finder, item, location) => (
    <div key={ md5(`${finder}${item}${location}`) }>
      {finderSpan(finder)} found their own {itemSpan(item)} at {locationSpan(location)}
    </div>
  )

  /** Hint message */
  static hintMessage = (finder, recipient, item, location, found) => (
    <div key={ md5(`${finder}${recipient}${item}${location}`) }>
      {recipientSpan(recipient, true)} {itemSpan(item)} can be found in {finderSpan(finder, true)}
      world at {locationSpan(location)} { found ? '(Found)' : null}
    </div>
  )
}

export default MonitorTools;
