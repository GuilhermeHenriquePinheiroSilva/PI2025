import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const authGuard: CanActivateFn = (route, state) => {
  const token = localStorage.getItem('access_token');
  const router = inject(Router);

  return token ? true : router.parseUrl('/login');
};
