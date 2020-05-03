import React from 'react';
import '../../../styles/HeaderBar/components/HeaderBar.scss';

const HeaderBar = () => (
  <div id="header-bar">
    Berserker&apos;s Multiworld WebUI v{ document.getElementById('app').getAttribute('data-version') }
  </div>
);

export default HeaderBar;
