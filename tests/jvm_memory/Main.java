package example;
import wros.scene.Scene;

public final class Main {
    static final class Node {
        final Node next;
        final int[] data;
        Node(int id, Node previous) {
            next = previous;
            data = new int[(id & 3) + 1];
            data[data.length - 1] = id;
        }
    }
    public static void main(String[] args) {
        if (args.length != 0 || Scene.abi() != 2) throw new AssertionError();
        Node head = null;
        for (int i = 0; i < 240; ++i) head = new Node(i, head);
        System.gc();
        int count = 0;
        for (Node node = head; node != null; node = node.next) count += node.data[node.data.length - 1];
        if (count != 28680) throw new AssertionError();
    }
}
