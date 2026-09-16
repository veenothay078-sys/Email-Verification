import React, { useState } from 'react';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import SingleVerify from './pages/SingleVerify';
import BatchAudit from './pages/BatchAudit';
import History from './pages/History';
import Analytics from './pages/Analytics';
import ApiDocs from './pages/ApiDocs';

export default function App() {
  const [currentTab, setCurrentTab] = useState('overview');

  const renderContent = () => {
    switch (currentTab) {
      case 'overview':
        return <Overview onNavigateToVerify={(tab) => setCurrentTab(tab)} />;
      case 'verify':
        return <SingleVerify />;
      case 'batch':
        return <BatchAudit />;
      case 'history':
        return <History />;
      case 'analytics':
        return <Analytics />;
      case 'api':
        return <ApiDocs />;
      default:
        return <Overview onNavigateToVerify={(tab) => setCurrentTab(tab)} />;
    }
  };

  return (
    <Layout currentTab={currentTab} onTabChange={setCurrentTab}>
      {renderContent()}
    </Layout>
  );
}
