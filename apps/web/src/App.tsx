/** Routes. Everything except /login sits behind <RequireAuth>. */

import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from '@/components/AppLayout'
import { RequireAuth } from '@/features/auth/RequireAuth'
import { ClientDetailPage } from '@/pages/ClientDetailPage'
import { ClientsPage } from '@/pages/ClientsPage'
import { CreditDetailPage } from '@/pages/CreditDetailPage'
import { CreditsPage } from '@/pages/CreditsPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { LoginPage } from '@/pages/LoginPage'
import { NewClientPage } from '@/pages/NewClientPage'
import { NewCreditPage } from '@/pages/NewCreditPage'
import { OverduePage } from '@/pages/OverduePage'
import { PaymentsPage } from '@/pages/PaymentsPage'
import { RegisterPaymentPage } from '@/pages/RegisterPaymentPage'
import { SettingsPage } from '@/pages/SettingsPage'

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/clientes" element={<ClientsPage />} />
        <Route path="/clientes/nuevo" element={<NewClientPage />} />
        <Route path="/clientes/:clientId" element={<ClientDetailPage />} />
        <Route path="/creditos" element={<CreditsPage />} />
        <Route path="/creditos/nuevo" element={<NewCreditPage />} />
        <Route path="/creditos/:creditId" element={<CreditDetailPage />} />
        <Route path="/creditos/:creditId/pagos/nuevo" element={<RegisterPaymentPage />} />
        <Route path="/pagos" element={<PaymentsPage />} />
        <Route path="/morosos" element={<OverduePage />} />
        <Route path="/configuracion" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
