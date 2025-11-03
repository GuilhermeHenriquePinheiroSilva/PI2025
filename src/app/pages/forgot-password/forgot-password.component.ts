import { Component } from '@angular/core';
import { AuthService } from '../../../services/auth.service';
import { NotificationService } from '../../../services/notification.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-forgot-password',
   standalone: true,
  imports: [
    CommonModule,
    FormsModule 
  ],
  templateUrl: './forgot-password.component.html',
  styleUrl: './forgot-password.component.css'
  // Adicione seus imports de standalone aqui
})
export class ForgotPasswordComponent {
  email: string = '';

  constructor(
    private authService: AuthService,
    private notificationService: NotificationService
  ) {}

  onSubmit(): void {
    this.authService.forgotPassword(this.email).subscribe({
      next: (res) => {
        this.notificationService.show(res.message, 'success');
      },
      error: (err) => {
        // Mesmo em caso de erro (ex: e-mail não encontrado), mostramos uma msg genérica por segurança
        this.notificationService.show('Se um usuário com este email existir, um link de redefinição foi enviado.', 'success');
      }
    });
  }
}