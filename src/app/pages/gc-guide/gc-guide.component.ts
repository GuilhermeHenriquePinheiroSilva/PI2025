import { Component } from '@angular/core';
import { FooterComponent } from '../shared/footer/footer.component';

@Component({
  selector: 'app-gc-guide',
  standalone: true,
  imports: [FooterComponent],
  templateUrl: './gc-guide.component.html',
  styleUrl: './gc-guide.component.css'
})
export class GcGuideComponent {

}
