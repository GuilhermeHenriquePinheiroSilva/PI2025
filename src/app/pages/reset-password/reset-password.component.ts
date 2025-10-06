import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../../services/auth.service';
import { NotificationService } from '../../../services/notification.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-reset-password',
   standalone: true,
  imports: [
    CommonModule,
    FormsModule 
  ],
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.css']
  // Adicione seus imports de standalone aqui
})
export class ResetPasswordComponent implements OnInit {
  newPassword = '';
  confirmPassword = '';
  private token = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService,
    private notificationService: NotificationService
  ) {}

  ngOnInit(): void {
    this.token = this.route.snapshot.queryParamMap.get('token') || '';
    if (!this.token) {
      this.notificationService.show('Token de redefinição inválido.', 'error');
      this.router.navigate(['/']); // Volta para a home
    }
  }

  hasUpperCase(password: string): boolean {
    return /[A-Z]/.test(password);
  }

  hasLowerCase(password: string): boolean {
    return /[a-z]/.test(password);
  }

  hasNumber(password: string): boolean {
    return /[0-9]/.test(password);
  }

  hasSpecialChar(password: string): boolean {
    return /[!@#$%^&*(),.?":{}|<>]/.test(password);
  }

  onSubmit(): void {
    if (this.newPassword !== this.confirmPassword) {
      this.notificationService.show('As senhas não coincidem.', 'warning');
      return;
    }

    this.authService.resetPassword(this.token, this.newPassword).subscribe({
      next: (res) => {
        this.notificationService.show(res.message, 'success');
        this.router.navigate(['/']); // Volta para a home/login
      },
      error: (err) => {
        this.notificationService.show(err.error.detail || 'Não foi possível redefinir a senha.', 'error');
      }
    });
  }
}