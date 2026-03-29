import React from 'react'
import './App.css'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import MainPage from './pages/main_page.jsx';
import UploadPage from './pages/upload_page.jsx';
import Header from './components/header.jsx';
import Footer from './components/footer.jsx';
import ViewMetrics from './pages/view_metrics_page.jsx';
import Insights from './pages/insights_page.jsx';
import AuthPage from './pages/auth_page.jsx';
import ProtectedRoute from './components/protected_route.jsx';

function AppShell() {
  const location = useLocation();
  const isAuthPage = location.pathname === '/auth';

  return (
      <div className='App'>
         {!isAuthPage && <Header/>}
         <div className={isAuthPage ? 'page-content auth-page-shell' : 'page-content'}>
        <Routes>
          <Route path='/' element= {<ViewMetrics/>}></Route>
          <Route path='/auth' element= {<AuthPage/>}></Route>
          <Route path='/landing' element= {<MainPage/>}></Route>
          <Route
            path='/upload'
            element={
              <ProtectedRoute>
                <UploadPage/>
              </ProtectedRoute>
            }
          ></Route>
          <Route path='/insights' element= {<Insights/>}></Route>
          <Route path='/view_metrics' element= {<ViewMetrics/>}></Route>  {/*change to viewMetrics when you set it up */}
        </Routes>
      
      </div>
      {!isAuthPage && <Footer/>}
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}

export default App
