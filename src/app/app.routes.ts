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
        path: 'product-page/:id', component: ProductPageComponent
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
        path: 'home', redirectTo: '', pathMatch: 'full'
    }
];