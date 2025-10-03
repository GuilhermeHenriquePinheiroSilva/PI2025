import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { SearchComponent } from './pages/search/search.component';
import { ProductPageComponent } from './pages/product-page/product-page.component';
import { CartComponent } from './pages/cart/cart.component';
import { EmptyCartComponent } from './pages/empty-cart/empty-cart.component';
import { authGuard } from './guard/auth.guard';
import { AddGcComponent } from './pages/add-gc/add-gc.component';
import { DashboardGcComponent } from './pages/dashboard-gc/dashboard-gc.component';
import { EditGcComponent } from './pages/edit-gc/edit-gc.component';
import { MyPurchasesComponent } from './pages/my-purchases/my-purchases.component';
import { enterpriseGuard } from './guard/enterprise.guard';
import { GcGuideComponent } from './pages/gc-guide/gc-guide.component';
import { UserProfileComponent } from './pages/user-profile/user-profile.component';
import { AdminDashboardComponent } from './pages/admin/admin-dashboard/admin-dashboard.component';
import { AdminGuard } from './guard/admin.guard';
import { ManageCategoriesComponent } from './pages/admin/manage-categories/manage-categories.component';
import { CategoryPageComponent } from './pages/category-page/category-page.component';
import { EmailVerificationComponent } from './pages/email-verification/email-verification.component';
import { ForgotPasswordComponent } from './pages/forgot-password/forgot-password.component';
import { ResetPasswordComponent } from './pages/reset-password/reset-password.component';
import { ValidateEnterprisesComponent } from './pages/admin/validate-enterprises/validate-enterprises.component';

export const routes: Routes = [
    {
        path: 'adicionar-gc', component: AddGcComponent,
        canActivate: [enterpriseGuard],
    },
    {
        path: 'editar-gc/:id', component: EditGcComponent,
        canActivate: [enterpriseGuard],
    },
    {
        path: 'dashboard-gc', component: DashboardGcComponent,
        canActivate: [enterpriseGuard]
    },
    {
        path: 'gc-guide', component: GcGuideComponent,
    },
    {
        path: 'search', component: SearchComponent
    },
    {
        path: 'search', component: SearchComponent
    },
    {
        path: 'admin',
        canActivate: [AdminGuard],
        children: [
            { path: '', component: AdminDashboardComponent, pathMatch: 'full' },
            { path: 'categories', component: ManageCategoriesComponent },
            { path: 'validate-enterprises', component: ValidateEnterprisesComponent }
        ]
    },
    {
        path: 'profile', component: UserProfileComponent
        // , canActivate: [authGuard]
    },
    {
        path: 'product-page/:id', component: ProductPageComponent
    },
    { 
        path: 'category/:id', component: CategoryPageComponent 
    },
    {
        path: 'empty-cart', component: EmptyCartComponent

        //, canActivate: [authGuard]
    },
    {
        path: 'cart', component: CartComponent
    },
    {
        path: 'minhas-compras', component: MyPurchasesComponent
    },
    {
        path: '', component: HomeComponent
    },
    {
         path: 'verify-email', component: EmailVerificationComponent
    },
    { 
        path: 'forgot-password', component: ForgotPasswordComponent
    },
    { 
        path: 'reset-password', component: ResetPasswordComponent 
    },
    {
        path: 'home', redirectTo: '', pathMatch: 'full'
    }
];