import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { NotificationService } from '../../services/notification.service';

export const authGuard: CanActivateFn = (route, state) => {
  const token = localStorage.getItem('access_token');
  const router = inject(Router);
  const notificationService = inject(NotificationService);

  if (token) {
    return true;
  } else {
    notificationService.show('Você precisa estar logado para acessar esta página.', 'warning');
    return router.parseUrl('/');
  }
};