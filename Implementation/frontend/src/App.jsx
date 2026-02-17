import { React, useState } from 'react'
import './App.css'
import {BrowserRouter, Routes, Route} from 'react-router-dom';
import MainPage from './pages/main_page.jsx';
import UploadPage from './pages/upload_page.jsx';
import Header from './components/header.jsx';
import Footer from './components/footer.jsx';
import BottleneckBanner from './components/bottleneck_banner.jsx';
import ViewMetrics from './pages/view_metrics_page.jsx'



function App() {

  return (
      <BrowserRouter>
      
      <div className='App'>
         <Header/>
         {/* <BottleneckBanner/> */}
         <div className="page-content">
        <Routes>
          <Route path='/' element= {<MainPage/>}></Route>
          <Route path='/upload' element= {<UploadPage/>}></Route>
          <Route path='/view_metrics' element= {<ViewMetrics/>}></Route>  {/*change to viewMetrics when you set it up */}
        </Routes>
      
      </div>
      <Footer/>
    </div>
      </BrowserRouter>


    
  )
}

export default App
