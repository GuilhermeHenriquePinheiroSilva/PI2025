// front/src/app/pages/email-verification/email-verification.component.ts

import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../../services/auth.service';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-email-verification',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './email-verification.component.html',
  styleUrls: ['./email-verification.component.css']
})
export class EmailVerificationComponent implements OnInit {
  message: string = 'Verificando sua conta, por favor, aguarde...';
  isSuccess: boolean = false;
  isLoading: boolean = true;

  constructor(
    private route: ActivatedRoute,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Pega o token da URL
    const token = this.route.snapshot.queryParamMap.get('token');

    if (token) {
      this.authService.verifyEmail(token).subscribe({
        next: (response) => {
          this.isSuccess = true;
          this.message = response.message || 'E-mail verificado com sucesso! Você já pode fazer o login.';
          this.isLoading = false;
        },
        error: (err) => {
          this.isSuccess = false;
          this.message = err.error.detail || 'Ocorreu um erro ao verificar seu e-mail. O link pode ter expirado.';
          this.isLoading = false;
        }
      });
    } else {
      this.message = 'Token de verificação não encontrado.';
      this.isLoading = false;
    }
  }

  navigateToLogin(): void {
    this.router.navigate(['/']); // Navegue para a página de login/home
  }
}