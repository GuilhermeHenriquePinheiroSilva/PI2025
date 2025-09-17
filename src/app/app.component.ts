import { Component, QueryList, AfterViewInit, ViewChildren, ElementRef, OnInit } from '@angular/core';
import VanillaTilt from 'vanilla-tilt';
import { RouterOutlet } from '@angular/router';
import { NavBarComponent } from './pages/shared/nav-bar/nav-bar.component';
import { FooterComponent } from './pages/shared/footer/footer.component';
import { NotificationPopupComponent } from './pages/shared/notification-popup/notification-popup.component';
import { ConfirmationPopupComponent } from './pages/shared/confirmation-popup/confirmation-popup.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    NavBarComponent,
    FooterComponent,
    NotificationPopupComponent,
    ConfirmationPopupComponent
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})


export class AppComponent implements AfterViewInit, OnInit {
  bodyMaiorQueTela : boolean = false;
  alturaTela : number = 0;
  alturaBody : number = 0;

  ngOnInit(): void {
    this.alturaTela = window.innerHeight;
    this.alturaBody = document.body.scrollHeight;

    if(this.alturaBody > this.alturaTela){
      this.bodyMaiorQueTela = true;
    }
    else{
      this.bodyMaiorQueTela = false;
    }
  }
  title = 'PI';
  srcNetflix = "/gift-cards/Netflix.png";
  srcGoogle = "/gift-cards/GooglePlay.png";
  srcSteam = "/gift-cards/Steam.png";

  @ViewChildren('tiltElement') tiltElements!: QueryList<ElementRef>;

  ngAfterViewInit() {
    this.tiltElements.forEach((elementRef) => {
      VanillaTilt.init(elementRef.nativeElement, {
        max: 25,
        speed: 400,
        reverse: true
      });
    });
  }
}