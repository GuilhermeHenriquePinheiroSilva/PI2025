// Front/src/app/guard/enterprise.guard.ts

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { map } from 'rxjs/operators';
import { of } from 'rxjs';

export const enterpriseGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Se não houver usuário, nega o acesso
  const currentUser = authService.getCurrentUser();
  if (!currentUser) {
    router.navigate(['/']);
    return false;
  }

  // Se o usuário não for do tipo ENTERPRISE, nega o acesso
  if (currentUser.role !== 'ENTERPRISE') {
    router.navigate(['/']); // Redireciona para a home
    return false;
  }

  // Se for um usuário ENTERPRISE, permite o acesso
  return true;
};