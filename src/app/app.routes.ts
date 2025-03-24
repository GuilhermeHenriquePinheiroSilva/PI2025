import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { SearchComponent } from './pages/search/search.component';
import { LoginComponent } from './pages/login/login.component';
import { RegisterComponent } from './pages/register/register.component';
import { ForgotPassComponent } from './pages/forgot-pass/forgot-pass.component';

export const routes: Routes = [
    {
        path: 'search', component: SearchComponent
    },
    {
        path: 'login', component: LoginComponent
    },
    {
        path: 'register', component: RegisterComponent
    },
    {
        path: 'forgot-password', component: ForgotPassComponent
    },
    {
        path: '', component: HomeComponent
    }
];
