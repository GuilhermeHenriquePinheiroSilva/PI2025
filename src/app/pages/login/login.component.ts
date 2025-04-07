import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../../services/auth.service';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    RouterLinkActive
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  email: string = '';
  password: string = '';
  errorMessage: string = '';

  constructor(private authService: AuthService, private router: Router) {}

  onSubmit() {
    this.authService.login(this.email, this.password).subscribe({
      next: (response) => {
        console.log('Login realizado com sucesso!', response);
        if (response.access_token && response.user) {
          localStorage.setItem('token', response.access_token);
          this.authService.setUser(response.user);
        }
        this.router.navigate(['/']);
      },
      error: (error) => {
        console.error('Erro no login', error);
        this.errorMessage = 'Email ou senha inválidos';
      }
    });
  }
}
