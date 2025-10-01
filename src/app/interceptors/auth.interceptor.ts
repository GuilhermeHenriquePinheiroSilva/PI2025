// auth.interceptor.ts

import { HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  // Pega o token do localStorage (onde ele foi salvo durante o login)
  const authToken = localStorage.getItem('authToken');

  // Se o token existir, clona a requisição e adiciona o cabeçalho de autorização
  if (authToken) {
    const authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${authToken}`
      }
    });
    // Envia a requisição clonada com o novo cabeçalho
    return next(authReq);
  }

  // Se não houver token, envia a requisição original sem modificação
  return next(req);
};
