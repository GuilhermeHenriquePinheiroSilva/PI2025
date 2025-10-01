import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Injectable({
    providedIn: 'root'
})
export class AdminGuard implements CanActivate {

    constructor(private authService: AuthService, private router: Router) { }

    // Front/src/app/guard/admin.guard.ts
    canActivate(): boolean {
        console.log('--- AdminGuard Ativado ---');

        const isAuthenticated = this.authService.isAuthenticated();
        const userRole = this.authService.getUserRole();

        console.log('AdminGuard - Autenticado?', isAuthenticated);
        console.log('AdminGuard - Role do usuário?', userRole);

        if (isAuthenticated && userRole === 'admin') {
            console.log('AdminGuard - Acesso PERMITIDO');
            return true;
        } else {
            console.log('AdminGuard - Acesso NEGADO. Redirecionando...');
            this.router.navigate(['/']);
            return false;
        }
    }
}