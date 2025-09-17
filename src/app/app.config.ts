import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';

// Importe as funções necessárias para o HttpClient e o Interceptor
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { authInterceptor } from './interceptors/auth.interceptor'; // Adapte o caminho se necessário

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }), 
    provideRouter(routes), 
    
    // Esta é a forma moderna e correta de fornecer o HttpClient
    // E, ao mesmo tempo, registrar o interceptor para ser usado em todas as requisições.
    provideHttpClient(withInterceptors([authInterceptor]))
  ]
};
