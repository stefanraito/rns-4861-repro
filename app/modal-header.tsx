import { BottomProbe } from '../components/BottomProbe';

// presentation: 'modal' + headerShown: true (see app/_layout.tsx). react-native-screens renders the
// header through a nested stack inside the modal (ScreenStackItem isHeaderInModal).
export default function ModalHeader() {
  return <BottomProbe title="Modal with native header" testPrefix="modal-header" />;
}
