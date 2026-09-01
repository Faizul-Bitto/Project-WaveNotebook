import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/base.css'
import './styles/header.css'
import './styles/footer.css'
import './styles/home.css'
import './styles/products.css'
import './styles/product-detail.css'
import './styles/cart.css'
import './styles/checkout.css'
import './styles/track-order.css'
import './styles/contact.css'
import './styles/offers.css'
import './styles/policy.css'
import './styles/admin/admin-login.css'
import './styles/admin/admin-layout.css'
import './styles/admin/admin-pages.css'
import './styles/admin/admin-product-form.css'
import './styles/admin/admin-attributes.css'
import './styles/admin/admin-orders.css'
import './styles/admin/admin-messages.css'
import './styles/animations.css'
import './styles/skeleton.css'
import './styles/transitions.css'
import './App.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)